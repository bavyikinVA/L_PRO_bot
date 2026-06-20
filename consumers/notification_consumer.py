import asyncio
import json
from datetime import datetime, timezone
from traceback import format_exception_only
from uuid import UUID, uuid4

from aiokafka import AIOKafkaConsumer
from loguru import logger
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from bot.utils import send_booking_notification
from config import settings
from database.database import async_session_maker
from database.models import Booking, ProcessedEvent
from events.booking import BOOKING_CANCELLED, BOOKING_CREATED, BOOKING_EVENTS_TOPIC
from events.kafka import KafkaEventProducer
from services.reminder_service import ReminderService

CONSUMER_NAME = "notification-consumer"
CONSUMER_GROUP_ID = "notification-service"


async def _mark_processed(session, *, event_id: UUID, event_type: str) -> bool:
    result = await session.execute(select(ProcessedEvent).where(ProcessedEvent.event_id == event_id))
    if result.scalar_one_or_none() is not None:
        return False

    session.add(ProcessedEvent(event_id=event_id, event_type=event_type, consumer_name=CONSUMER_NAME))
    try:
        await session.flush()
        return True
    except IntegrityError:
        await session.rollback()
        return False


async def handle_booking_created(event: dict) -> None:
    event_id = UUID(event["event_id"])
    event_type = event["event_type"]
    payload = event["payload"]
    booking_id = payload["booking_id"]

    async with async_session_maker() as session:
        should_process = await _mark_processed(session, event_id=event_id, event_type=event_type)
        if not should_process:
            logger.info(
                "[KAFKA-CONSUMER] duplicate skipped consumer={} event_id={} event_type={}",
                CONSUMER_NAME,
                event_id,
                event_type,
            )
            return

        result = await session.execute(
            select(Booking)
            .options(joinedload(Booking.user), joinedload(Booking.service), joinedload(Booking.specialist))
            .where(Booking.id == booking_id)
        )
        booking = result.scalars().first()
        if booking is None:
            logger.warning(
                "[KAFKA-CONSUMER] booking not found consumer={} event_id={} event_type={} booking_id={}",
                CONSUMER_NAME,
                event_id,
                event_type,
                booking_id,
            )
            await session.commit()
            return

        booking_datetime = datetime.fromisoformat(payload["booking_datetime"])
        await send_booking_notification(
            user_id=payload.get("telegram_id"),
            specialist_name=payload["specialist_name"],
            service_name=payload["service_name"],
            booking_datetime=booking_datetime,
            client_full_name=payload.get("client_full_name"),
            client_phone=payload.get("client_phone"),
        )
        await ReminderService.create_reminders_for_booking(session=session, booking=booking)
        await session.commit()
        logger.info(
            "[KAFKA-CONSUMER] processed consumer={} event_id={} event_type={} booking_id={} telegram_id={}",
            CONSUMER_NAME,
            event_id,
            event_type,
            booking_id,
            payload.get("telegram_id"),
        )


async def handle_booking_cancelled(event: dict) -> None:
    event_id = UUID(event["event_id"])
    event_type = event["event_type"]
    payload = event["payload"]
    booking_id = payload["booking_id"]

    async with async_session_maker() as session:
        should_process = await _mark_processed(session, event_id=event_id, event_type=event_type)
        if not should_process:
            logger.info(
                "[KAFKA-CONSUMER] duplicate skipped consumer={} event_id={} event_type={}",
                CONSUMER_NAME,
                event_id,
                event_type,
            )
            return

        await ReminderService.cancel_reminders_for_booking(session, booking_id)
        await session.commit()
        logger.info(
            "[KAFKA-CONSUMER] processed consumer={} event_id={} event_type={} booking_id={}",
            CONSUMER_NAME,
            event_id,
            event_type,
            booking_id,
        )


async def handle_event(event: dict) -> None:
    event_type = event.get("event_type")
    if event_type == BOOKING_CREATED:
        await handle_booking_created(event)
    elif event_type == BOOKING_CANCELLED:
        await handle_booking_cancelled(event)
    else:
        logger.debug("[KAFKA-CONSUMER] ignored event_type={} event_id={}", event_type, event.get("event_id"))


async def handle_event_with_retries(event: dict) -> None:
    max_retries = max(1, settings.KAFKA_CONSUMER_MAX_RETRIES)
    retry_delay = max(0, settings.KAFKA_CONSUMER_RETRY_DELAY_SECONDS)

    for attempt in range(1, max_retries + 1):
        try:
            await handle_event(event)
            if attempt > 1:
                logger.info(
                    "[KAFKA-CONSUMER] retry succeeded consumer={} event_id={} event_type={} attempt={}/{}",
                    CONSUMER_NAME,
                    event.get("event_id"),
                    event.get("event_type"),
                    attempt,
                    max_retries,
                )
            return
        except Exception as exc:
            if attempt >= max_retries:
                logger.exception(
                    "[KAFKA-CONSUMER] retries exhausted consumer={} event_id={} event_type={} attempt={}/{} error={}",
                    CONSUMER_NAME,
                    event.get("event_id"),
                    event.get("event_type"),
                    attempt,
                    max_retries,
                    exc,
                )
                raise

            logger.warning(
                "[KAFKA-CONSUMER] retry scheduled consumer={} event_id={} event_type={} attempt={}/{} retry_in={}s error={}",
                CONSUMER_NAME,
                event.get("event_id"),
                event.get("event_type"),
                attempt,
                max_retries,
                retry_delay,
                exc,
            )
            if retry_delay > 0:
                await asyncio.sleep(retry_delay)


async def publish_to_dlq(
    producer: KafkaEventProducer,
    *,
    original_event: dict,
    message,
    error: Exception,
) -> None:
    event_id = original_event.get("event_id") or str(uuid4())
    event_type = original_event.get("event_type", "unknown")
    booking_id = original_event.get("payload", {}).get("booking_id")
    error_message = "".join(format_exception_only(type(error), error)).strip()

    dlq_event = {
        "dlq_event_id": str(uuid4()),
        "failed_at": datetime.now(timezone.utc).isoformat(),
        "consumer_name": CONSUMER_NAME,
        "consumer_group_id": CONSUMER_GROUP_ID,
        "original_topic": message.topic,
        "original_partition": message.partition,
        "original_offset": message.offset,
        "original_key": message.key,
        "error_type": type(error).__name__,
        "error_message": error_message,
        "original_event": original_event,
    }

    await producer.send(
        topic=settings.KAFKA_BOOKING_EVENTS_DLQ_TOPIC,
        key=str(message.key or booking_id or event_id),
        value=dlq_event,
    )
    logger.error(
        "[KAFKA-DLQ] published dlq_event_id={} original_event_id={} event_type={} booking_id={} topic={} original_offset={} error_type={} error_message={}",
        dlq_event["dlq_event_id"],
        event_id,
        event_type,
        booking_id,
        settings.KAFKA_BOOKING_EVENTS_DLQ_TOPIC,
        message.offset,
        type(error).__name__,
        error_message,
    )


async def main() -> None:
    consumer = AIOKafkaConsumer(
        BOOKING_EVENTS_TOPIC,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id=CONSUMER_GROUP_ID,
        enable_auto_commit=False,
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
        key_deserializer=lambda value: value.decode("utf-8") if value else None,
        auto_offset_reset="earliest",
    )
    dlq_producer = KafkaEventProducer()

    await consumer.start()
    await dlq_producer.start()
    logger.info(
        "[KAFKA-CONSUMER] started consumer={} group_id={} topic={} bootstrap_servers={} max_retries={} retry_delay={}s dlq_topic={}",
        CONSUMER_NAME,
        CONSUMER_GROUP_ID,
        BOOKING_EVENTS_TOPIC,
        settings.KAFKA_BOOTSTRAP_SERVERS,
        settings.KAFKA_CONSUMER_MAX_RETRIES,
        settings.KAFKA_CONSUMER_RETRY_DELAY_SECONDS,
        settings.KAFKA_BOOKING_EVENTS_DLQ_TOPIC,
    )
    try:
        async for message in consumer:
            event = message.value
            event_type = event.get("event_type")
            event_id = event.get("event_id")
            booking_id = event.get("payload", {}).get("booking_id")
            logger.info(
                "[KAFKA-CONSUMER] received topic={} partition={} offset={} key={} event_id={} event_type={} booking_id={}",
                message.topic,
                message.partition,
                message.offset,
                message.key,
                event_id,
                event_type,
                booking_id,
            )
            try:
                await handle_event_with_retries(event)
                await consumer.commit()
                logger.debug("[KAFKA-CONSUMER] committed event_id={} event_type={}", event_id, event_type)
            except Exception as exc:
                logger.exception(
                    "[KAFKA-CONSUMER] processing failed, sending to DLQ topic={} partition={} offset={} event_id={} event_type={} error={}",
                    message.topic,
                    message.partition,
                    message.offset,
                    event_id,
                    event_type,
                    exc,
                )
                await publish_to_dlq(dlq_producer, original_event=event, message=message, error=exc)
                await consumer.commit()
                logger.warning(
                    "[KAFKA-CONSUMER] committed after DLQ event_id={} event_type={} original_topic={} original_offset={}",
                    event_id,
                    event_type,
                    message.topic,
                    message.offset,
                )
    finally:
        await consumer.stop()
        await dlq_producer.stop()
        logger.info("[KAFKA-CONSUMER] stopped consumer={}", CONSUMER_NAME)


if __name__ == "__main__":
    asyncio.run(main())
