from typing import Optional

from fastapi import HTTPException
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from api.dao import UserDAO
from api.schemas import UserModel, UserUpdateModel
from core.encryption import encryption_service, make_hash
from core.validators import normalize_phone, validate_name, normalize_text
from database.models import User


class UserService:
    @staticmethod
    def user_to_model(user: User) -> UserModel:
        return UserModel(
            id=user.id,
            telegram_id=user.telegram_id,
            username=user.decrypted_username,
            first_name=user.decrypted_first_name,
            last_name=user.decrypted_last_name,
            patronymic=user.decrypted_patronymic,
            phone_number=user.decrypted_phone_number,
            is_admin=user.is_admin,
        )

    @staticmethod
    async def create_user(session: AsyncSession, user_data: UserModel) -> UserModel:
        logger.info("Создание пользователя")

        try:
            if not user_data.phone_number:
                raise HTTPException(status_code=400, detail="Номер телефона обязателен")

            if not user_data.first_name:
                raise HTTPException(status_code=400, detail="Имя обязательно")

            normalized_phone = normalize_phone(user_data.phone_number)
            first_name = validate_name(user_data.first_name, "Имя")
            last_name = validate_name(user_data.last_name, "Фамилия")
            patronymic = validate_name(user_data.patronymic, "Отчество")
            username = normalize_text(user_data.username)

            phone_hash = make_hash(normalized_phone)

            result = await session.execute(
                select(User).where(phone_hash == User.phone_hash)
            )
            existing_user = result.scalars().first()

            if existing_user:
                raise HTTPException(
                    status_code=400,
                    detail="Пользователь с таким номером телефона уже существует"
                )

            new_user = User(
                telegram_id=user_data.telegram_id,
                is_admin=user_data.is_admin,
            )

            new_user.set_private_data(
                first_name=first_name or "",
                last_name=last_name,
                patronymic=patronymic,
                phone_number=normalized_phone,
                username=username,
            )

            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)

            logger.info(f"User created: {new_user.id}")

            return UserService.user_to_model(new_user)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ошибка при создании пользователя: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail="Ошибка при создании пользователя")

    @staticmethod
    async def update_user(
        session: AsyncSession,
        user_id: int,
        update_data: UserUpdateModel
    ) -> UserModel:
        logger.info(f"Обновление пользователя ID {user_id}")

        try:
            user = await UserDAO.find_one_or_none_by_id(
                session=session,
                data_id=user_id
            )

            if user is None:
                raise HTTPException(status_code=404, detail="Пользователь не найден")

            update_dict = update_data.model_dump(exclude_unset=True)

            if "telegram_id" in update_dict:
                user.telegram_id = update_dict["telegram_id"]

            if "is_admin" in update_dict:
                user.is_admin = update_dict["is_admin"]

            if "username" in update_dict:
                username = normalize_text(update_dict["username"])
                user.username = encryption_service.encrypt(username)

            session.add(user)
            await session.commit()
            await session.refresh(user)

            return UserService.user_to_model(user)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ошибка при обновлении пользователя: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail="Ошибка при обновлении пользователя")

    @staticmethod
    async def create_user_by_admin(
        session: AsyncSession,
        user_data: UserModel
    ) -> UserModel:
        logger.info("Создание клиента админом")

        if not user_data.phone_number:
            raise HTTPException(status_code=400, detail="Номер телефона обязателен")

        if not user_data.first_name:
            raise HTTPException(status_code=400, detail="Имя обязательно")

        normalized_phone = normalize_phone(user_data.phone_number)
        first_name = validate_name(user_data.first_name, "Имя")
        last_name = validate_name(user_data.last_name, "Фамилия")
        patronymic = validate_name(user_data.patronymic, "Отчество")
        username = normalize_text(user_data.username)

        phone_hash = make_hash(normalized_phone)

        result = await session.execute(
            select(User).where(phone_hash == User.phone_hash)
        )
        existing_user = result.scalars().first()

        if existing_user:
            return UserService.user_to_model(existing_user)

        new_user = User(
            telegram_id=user_data.telegram_id,
            is_admin=user_data.is_admin,
        )

        new_user.set_private_data(
            first_name=first_name or "",
            last_name=last_name,
            patronymic=patronymic,
            phone_number=normalized_phone,
            username=username,
        )

        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

        return UserService.user_to_model(new_user)

    @staticmethod
    async def get_user_by_telegram_id(
        session: AsyncSession,
        telegram_id: int
    ) -> Optional[UserModel]:
        logger.info(f"Получение пользователя Telegram ID {telegram_id}")

        try:
            result = await session.execute(
                select(User)
                .options(joinedload(User.bookings))
                .where(telegram_id == User.telegram_id)
            )

            user = result.scalars().first()

            if user:
                return UserService.user_to_model(user)

            return None

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ошибка при получении пользователя: {str(e)}")
            raise HTTPException(status_code=500, detail="Ошибка при получении пользователя")