from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, field_validator


class BookingModel(BaseModel):
    id: Optional[int] = None
    specialist_id: int
    user_id: int
    service_id: int
    booking_datetime: datetime
    duration_minutes: int # длительность берем из услуги или расписания
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    reminder_24h_task_id: Optional[str] = None
    reminder_6h_task_id: Optional[str] = None
    reminder_1h_task_id: Optional[str] = None
    is_cancelled: bool = False
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    @field_validator("booking_datetime", "created_at")
    def ensure_timezone(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=ZoneInfo("UTC"))
        return v