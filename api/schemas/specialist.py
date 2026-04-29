from pydantic import BaseModel, ConfigDict
from typing import Optional


class SpecialistCreate(BaseModel):
    first_name: str
    last_name: str
    work_experience: str
    photo: str

    model_config = ConfigDict(from_attributes=True)


class SpecialistModel(BaseModel):
    id: int
    first_name: str
    last_name: str
    work_experience: Optional[str] = None
    photo: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class SpecialistUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    work_experience: Optional[str] = None
    photo: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
