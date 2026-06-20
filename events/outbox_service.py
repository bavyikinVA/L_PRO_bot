from sqlalchemy.ext.asyncio import AsyncSession

from database.models import OutboxEvent
from events.base import EventEnvelope


class OutboxService:
    @staticmethod
    async def add_event(
        session: AsyncSession,
        *,
        topic: str,
        key: str,
        aggregate_type: str,
        aggregate_id: str | int,
        event: EventEnvelope,
    ) -> OutboxEvent:
        outbox_event = OutboxEvent(
            id=event.event_id,
            topic=topic,
            event_key=key,
            aggregate_type=aggregate_type,
            aggregate_id=str(aggregate_id),
            event_type=event.event_type,
            event_version=event.event_version,
            payload=event.model_dump(mode="json"),
            headers={
                "producer": event.producer,
                "correlation_id": str(event.correlation_id),
                "causation_id": str(event.causation_id) if event.causation_id else None,
            },
            status="pending",
        )
        session.add(outbox_event)
        return outbox_event
