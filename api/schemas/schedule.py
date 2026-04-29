from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date, time


class SpecialistScheduleModel(BaseModel):
    id: Optional[int] = None
    specialist_id: int
    work_date: date
    start_time: time
    end_time: time
    is_working: bool = True
    slot_duration_minutes: int = 120
    model_config = ConfigDict(from_attributes=True)