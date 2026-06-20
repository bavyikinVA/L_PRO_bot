import asyncio
import json
from datetime import datetime
from uuid import UUID

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
from services.reminder_service import ReminderService

CONSUMER_NAME = "notification-consumer"


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
            logger.info("[KAFKA-CONSUMER] duplicate skipped consumer={} event_id={} event_type={}", CONSUMER_NAME, event_id, event_type)
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
            logger.info("[KAFKA-CONSUMER] duplicate skipped consumer={} event_id={} event_type={}", CONSUMER_NAME, event_id, event_type)
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


async def main() -> None:
    consumer = AIOKafkaConsumer(
        BOOKING_EVENTS_TOPIC,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="notification-service",
        enable_auto_commit=False,
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
        key_deserializer=lambda value: value.decode("utf-8") if value else None,
        auto_offset_reset="earliest",
    )

    await consumer.start()
    logger.info(
        "[KAFKA-CONSUMER] started consumer={} group_id={} topic={} bootstrap_servers={}",
        CONSUMER_NAME,
        "notification-service",
        BOOKING_EVENTS_TOPIC,
        settings.KAFKA_BOOTSTRAP_SERVERS,
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
                if event_type == BOOKING_CREATED:
                    await handle_booking_created(event)
                elif event_type == BOOKING_CANCELLED:
                    await handle_booking_cancelled(event)
                else:
                    logger.debug("[KAFKA-CONSUMER] ignored event_type={} event_id={}", event_type, event_id)

                await consumer.commit()
                logger.debug("[KAFKA-CONSUMER] committed event_id={} event_type={}", event_id, event_type)
            except Exception as exc:
                logger.exception(
                    "[KAFKA-CONSUMER] processing failed topic={} partition={} offset={} event_id={} event_type={} error={}",
                    message.topic,
                    message.partition,
                    message.offset,
                    event_id,
                    event_type,
                    exc,
                )
                # Offset не коммитим: Kafka сможет доставить сообщение повторно.
                await asyncio.sleep(5)
    finally:
        await consumer.stop()
        logger.info("[KAFKA-CONSUMER] stopped consumer={}", CONSUMER_NAME)


if __name__ == "__main__":
    asyncio.run(main())
