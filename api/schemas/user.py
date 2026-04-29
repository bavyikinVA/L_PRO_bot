from pydantic import BaseModel, ConfigDict
from typing import Optional


class TelegramIDModel(BaseModel):
    telegram_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class UserModel(TelegramIDModel):
    id: Optional[int] = None
    telegram_id : Optional[int] = None
    username: Optional[str] = None
    first_name: str
    last_name: Optional[str] = None
    patronymic: Optional[str] = None
    phone_number: Optional[str] = None
    is_admin: bool = False
    model_config = ConfigDict(from_attributes=True)


class UserUpdateModel(BaseModel):
    telegram_id: Optional[int] = None
    username: Optional[str] = None
    is_admin: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)