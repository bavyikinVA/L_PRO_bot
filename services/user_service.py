from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from sqlalchemy.orm import joinedload

from api.dao import UserDAO
from api.schemas import UserModel, UserUpdateModel
from database.models import User


class UserService:
    @staticmethod
    async def create_user(session: AsyncSession, user_data: UserModel) -> UserModel:
        logger.info(f"Создание пользователя: {user_data.model_dump()}")
        try:
            if user_data.phone_number is None:
                raise HTTPException(status_code=400, detail="Номер телефона обязателен")
            if user_data.first_name is None:
                raise HTTPException(status_code=400, detail="Имя обязательно")

            existing_user = await UserDAO.find_one_or_none(
                session=session,
                filters=UserModel(
                    first_name=user_data.first_name,
                    last_name=user_data.last_name,
                    phone_number=user_data.phone_number
                ))

            if existing_user:
                raise HTTPException(
                    status_code=400,
                    detail="Пользователь с такими данными уже существует"
                )
            logger.debug(f"Creating new user {existing_user}")
            new_user = await UserDAO.add(
                session=session,
                values=user_data,
                commit=True
            )
            if not new_user:
                logger.error("UserDAO.add returned None")
                raise HTTPException(status_code=500, detail="Не удалось создать пользователя")
            logger.info(f"User created: {new_user.id}")
            return UserModel.model_validate(new_user)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ошибка при создании пользователя: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Ошибка при создании пользователя: {str(e)}")


    @staticmethod
    async def update_user(session: AsyncSession, user_id: int, update_data: UserUpdateModel) -> UserModel:
        logger.info(f"Обновление пользователя ID {user_id}: {update_data.model_dump()}")
        try:
            updated_count = await UserDAO.update(
                session=session,
                filters={"id": user_id},
                values=update_data.model_dump(exclude_unset=True),
                commit=True
            )
            if updated_count == 0:
                raise HTTPException(status_code=404, detail="Пользователь не найден")
            updated_user = await UserDAO.find_one_or_none_by_id(session=session, data_id=user_id)
            if updated_user is None:
                raise HTTPException(status_code=404, detail="Пользователь не найден после обновления")
            logger.debug(f"Updated user: {updated_user.__dict__}")
            return UserModel.model_validate(updated_user)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ошибка при обновлении пользователя: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail="Ошибка при обновлении пользователя")


    @staticmethod
    async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> Optional[UserModel] or None:
        logger.info(f"Получение пользователя Telegram ID {telegram_id}")
        try:
            result = await session.execute(
                select(User)
                .options(joinedload(User.bookings))
                .where(telegram_id == User.telegram_id)
            )
            user = result.scalars().first()
            if user:
                return UserModel.model_validate(user)
            else:
                return None
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ошибка при получении пользователя: {str(e)}")
            raise HTTPException(status_code=500, detail="Ошибка при получении пользователя")