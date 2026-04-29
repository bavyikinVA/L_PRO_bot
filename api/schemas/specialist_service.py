from pydantic import BaseModel, ConfigDict


class SpecialistServiceCreate(BaseModel):
    specialist_id: int
    service_id: int
    model_config = ConfigDict(from_attributes=True)


class SpecialistServiceModel(BaseModel):
    specialist_id: int
    service_id: int
    model_config = ConfigDict(from_attributes=True)