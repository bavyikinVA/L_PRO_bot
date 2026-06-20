from datetime import datetime
from uuid import UUID, uuid4

from events.base import EventEnvelope

BOOKING_EVENTS_TOPIC = "lpro.booking.events"
BOOKING_CREATED = "booking.created"
BOOKING_CANCELLED = "booking.cancelled"


def build_booking_created_event(
    *,
    booking_id: int,
    user_id: int,
    telegram_id: int | None,
    client_full_name: str | None,
    client_phone: str | None,
    service_id: int,
    service_name: str,
    specialist_id: int,
    specialist_name: str,
    booking_datetime: datetime,
    duration_minutes: int,
    correlation_id: UUID | None = None,
) -> EventEnvelope:
    return EventEnvelope(
        event_type=BOOKING_CREATED,
        producer="booking-service",
        correlation_id=correlation_id or uuid4(),
        payload={
            "booking_id": booking_id,
            "user_id": user_id,
            "telegram_id": telegram_id,
            "client_full_name": client_full_name,
            "client_phone": client_phone,
            "service_id": service_id,
            "service_name": service_name,
            "specialist_id": specialist_id,
            "specialist_name": specialist_name,
            "booking_datetime": booking_datetime.isoformat(),
            "duration_minutes": duration_minutes,
        },
    )


def build_booking_cancelled_event(
    *,
    booking_id: int,
    user_id: int,
    telegram_id: int | None,
    service_id: int,
    specialist_id: int,
    booking_datetime: datetime,
    correlation_id: UUID | None = None,
) -> EventEnvelope:
    return EventEnvelope(
        event_type=BOOKING_CANCELLED,
        producer="booking-service",
        correlation_id=correlation_id or uuid4(),
        payload={
            "booking_id": booking_id,
            "user_id": user_id,
            "telegram_id": telegram_id,
            "service_id": service_id,
            "specialist_id": specialist_id,
            "booking_datetime": booking_datetime.isoformat(),
        },
    )
