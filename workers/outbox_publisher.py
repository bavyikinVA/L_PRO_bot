import asyncio
import signal
from datetime import datetime, timezone

from loguru import logger
from sqlalchemy import select

from config import settings
from database.database import async_session_maker
from database.models import OutboxEvent
from events.kafka import KafkaEventProducer

_shutdown_requested = asyncio.Event()


def _request_shutdown() -> None:
    logger.info("[OUTBOX] shutdown requested")
    _shutdown_requested.set()


async def publish_pending_events(producer: KafkaEventProducer) -> int:
    """Publish one batch of pending/failed outbox events.

    Producer is passed from main() and stays alive for the whole worker lifetime.
    This avoids noisy and expensive start/stop cycles every polling iteration.
    """
    published_count = 0

    async with async_session_maker() as session:
        result = await session.execute(
            select(OutboxEvent)
            .where(OutboxEvent.status.in_(["pending", "failed"]))
            .order_by(OutboxEvent.created_at)
            .limit(settings.OUTBOX_BATCH_SIZE)
        )
        events = result.scalars().all()

        if not events:
            logger.debug("[OUTBOX] no pending events")
            return 0

        logger.info("[OUTBOX] batch loaded count={}", len(events))

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
                    "[OUTBOX] published event_id={} event_type={} aggregate={}:{} topic={} key={}",
                    event.id,
                    event.event_type,
                    event.aggregate_type,
                    event.aggregate_id,
                    event.topic,
                    event.event_key,
                )
            except Exception as exc:
                event.status = "failed"
                event.error_message = str(exc)
                logger.exception(
                    "[OUTBOX] publish failed event_id={} event_type={} aggregate={}:{} topic={} error={}",
                    event.id,
                    event.event_type,
                    event.aggregate_type,
                    event.aggregate_id,
                    event.topic,
                    exc,
                )

        await session.commit()
        return published_count


async def main() -> None:
    logger.info(
        "[OUTBOX] publisher started bootstrap_servers={} poll_interval={}s batch_size={}",
        settings.KAFKA_BOOTSTRAP_SERVERS,
        settings.OUTBOX_POLL_INTERVAL_SECONDS,
        settings.OUTBOX_BATCH_SIZE,
    )

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _request_shutdown)
        except NotImplementedError:
            # Windows compatibility for local runs. Docker/Linux supports signal handlers.
            pass

    producer = KafkaEventProducer()
    await producer.start()

    try:
        while not _shutdown_requested.is_set():
            try:
                await publish_pending_events(producer)
            except Exception as exc:
                logger.exception("[OUTBOX] iteration failed error={}", exc)

            try:
                await asyncio.wait_for(
                    _shutdown_requested.wait(),
                    timeout=settings.OUTBOX_POLL_INTERVAL_SECONDS,
                )
            except asyncio.TimeoutError:
                pass
    finally:
        await producer.stop()
        logger.info("[OUTBOX] publisher stopped")


if __name__ == "__main__":
    asyncio.run(main())
