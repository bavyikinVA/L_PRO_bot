from pydantic import BaseModel, ConfigDict
from typing import Optional


class ServiceCreate(BaseModel):
    description: str
    label: str
    price: int
    duration_minutes: int
    model_config = ConfigDict(from_attributes=True)


class ServiceUpdate(BaseModel):
    label: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = None
    duration_minutes: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


class ServiceModel(BaseModel):
    id: int
    label: str
    description: str
    price: int
    duration_minutes: int
    model_config = ConfigDict(from_attributes=True)
