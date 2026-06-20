import asyncio
from datetime import datetime, timezone

from loguru import logger
from sqlalchemy import select

from config import settings
from database.database import async_session_maker
from database.models import OutboxEvent
from events.kafka import KafkaEventProducer


async def publish_pending_events() -> int:
    producer = KafkaEventProducer()
    await producer.start()
    published_count = 0

    try:
        async with async_session_maker() as session:
            result = await session.execute(
                select(OutboxEvent)
                .where(OutboxEvent.status.in_(["pending", "failed"]))
                .order_by(OutboxEvent.created_at)
                .limit(settings.OUTBOX_BATCH_SIZE)
            )
            events = result.scalars().all()

            for event in events:
                try:
                    await producer.send(
                        topic=event.topic,
                        key=event.event_key,
                        value=event.payload,
                    )
                    event.status = "published"
                    event.published_at = datetime.now(timezone.utc)
                    event.error_message = None
                    published_count += 1
                    logger.info(
                        f"Published outbox event id={event.id} type={event.event_type} topic={event.topic}"
                    )
                except Exception as exc:
                    event.status = "failed"
                    event.error_message = str(exc)
                    logger.exception(f"Failed to publish outbox event id={event.id}: {exc}")

            await session.commit()
            return published_count
    finally:
        await producer.stop()


async def main() -> None:
    logger.info("Outbox publisher started")
    while True:
        try:
            await publish_pending_events()
        except Exception as exc:
            logger.exception(f"Outbox publisher iteration failed: {exc}")
        await asyncio.sleep(settings.OUTBOX_POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(main())
