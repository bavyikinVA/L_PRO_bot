from datetime import date, datetime
from typing import Dict, Any, List
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from loguru import logger
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from api.dao import BookingDAO, SpecialistDAO, ServiceDAO, UserDAO
from api.schemas import BookingModel
from bot.utils import send_booking_notification
from database.database import async_session_maker
from database.models import Booking, SpecialistService
from services.reminder_service import ReminderService
from services.user_service import UserService

MSK = ZoneInfo("Europe/Moscow")


class BookingService:
    @staticmethod
    async def create_booking(session: AsyncSession, booking_data: BookingModel) -> BookingModel:
        logger.info(f'Создание брони: specialist_id={booking_data.specialist_id}, '
                    f'user_id={booking_data.user_id}, service_id={booking_data.service_id}, '
                    f'datetime={booking_data.booking_datetime}, timezone={booking_data.booking_datetime.tzinfo}')

        try:
            logger.debug(f"Поиск специалиста ID: {booking_data.specialist_id}")
            specialist = await SpecialistDAO.find_one_or_none_by_id(data_id=booking_data.specialist_id, session=session)
            if specialist is None:
                logger.warning(f"Специалист не найден: ID {booking_data.specialist_id}")
                raise HTTPException(status_code=404, detail="Специалист не найден")
            logger.debug(f"Специалист найден: {specialist.first_name} {specialist.last_name}")

            logger.debug(f"Поиск услуги ID: {booking_data.service_id}")
            service = await ServiceDAO.find_one_or_none_by_id(data_id=booking_data.service_id, session=session)
            if service is None:
                logger.warning(f"Услуга не найдена: ID {booking_data.service_id}")
                raise HTTPException(status_code=404, detail="Услуга не найдена")
            logger.debug(f"Услуга найдена: {service.label}")

            logger.debug(f"Поиск пользователя ID: {booking_data.user_id}")
            user = await UserDAO.find_one_or_none_by_id(data_id=booking_data.user_id, session=session)
            if user is None:
                logger.warning(f"Пользователь не найден: ID {booking_data.user_id}")
                raise HTTPException(status_code=404, detail="Клиент не найден")
            logger.debug(f"Пользователь найден: {user.first_name} {user.last_name}")

            logger.debug(
                f"Проверка связи специалист-услуга: specialist_id={booking_data.specialist_id}, "
                f"service_id={booking_data.service_id}")
            result = await session.execute(
                select(SpecialistService)
                .where(
                    booking_data.specialist_id == SpecialistService.specialist_id,
                    booking_data.service_id == SpecialistService.service_id
                )
            )
            specialist_service = result.scalar_one_or_none()
            if not specialist_service:
                logger.warning(
                    f"Специалист ID {booking_data.specialist_id} не предоставляет услугу ID {booking_data.service_id}")
                raise HTTPException(
                    status_code=400,
                    detail="Данный специалист не предоставляет указанную услугу"
                )
            logger.debug(f"Связь специалист-услуга подтверждена")

            logger.info(f"Создание брони через BookingDAO")
            new_booking = await BookingDAO.book_appointment(
                session=session,
                specialist_id=booking_data.specialist_id,
                user_id=booking_data.user_id,
                service_id=booking_data.service_id,
                booking_datetime=booking_data.booking_datetime
            )
            logger.success(f"Бронь создана успешно: ID {new_booking.id}, datetime={new_booking.booking_datetime}")

            booking_result = BookingModel.model_validate(new_booking)

            try:
                logger.debug(f"Отправка уведомления пользователю Telegram ID: {user.telegram_id}")
                notification_time = new_booking.booking_datetime.astimezone(MSK)
                logger.debug(f'Время для уведомления (MSK): {notification_time}')
                client_full_name = " ".join(
                    part for part in [
                        user.last_name,
                        user.first_name,
                        user.patronymic
                    ]
                    if part
                )

                await send_booking_notification(
                    user_id=user.telegram_id,
                    specialist_name=f"{specialist.first_name} {specialist.last_name}",
                    service_name=service.label,
                    booking_datetime=notification_time,
                    client_full_name=client_full_name,
                    client_phone=user.phone_number
                )
                logger.debug(f"Уведомление отправлено успешно")
            except Exception as notify_error:
                logger.error(f"Ошибка при отправке уведомления: {str(notify_error)}")

            try:
                await ReminderService.create_reminders_for_booking(session=session, booking=new_booking)
            except Exception as reminder_error:
                logger.warning(f'Ошибка при планировании напоминаний: {str(reminder_error)}')

            return booking_result

        except Exception as e:
            await session.rollback()
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(status_code=500, detail="Ошибка при создании бронирования")


    @staticmethod
    async def get_available_slots(
            session: AsyncSession,
            specialist_id: int,
            start_date: date,
            service_id: int
    ) -> Dict[str, Any]:
        logger.info(f"Получение доступных слотов для специалиста ID {specialist_id} с {start_date}")
        return await BookingDAO.get_available_slots(
            session=session,
            specialist_id=specialist_id,
            start_date=start_date,
            service_id=service_id)


    @staticmethod
    async def get_booking(session: AsyncSession, booking_id: int) -> Booking:
        logger.info(f"Получение бронирования ID {booking_id}")
        try:
            result = await session.execute(
                select(Booking)
                .options(
                    joinedload(Booking.specialist),
                    joinedload(Booking.service),
                    joinedload(Booking.user)
                )
                .where(booking_id == Booking.id)
            )
            booking = result.scalars().first()
            if not booking:
                logger.warning(f"Бронирование не найдено для ID: {booking_id}")
                raise HTTPException(status_code=404, detail="Бронирование не найдено")

            logger.debug(f"Найдено бронирование ID: {booking.id}, "
                         f"дата: {booking.booking_datetime}, статус: {booking.status}")
            logger.success(f"Успешно получено бронирование")

            return booking
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ошибка при получении бронирования: {str(e)}")
            logger.exception("Полная трассировка ошибки:")
            raise HTTPException(status_code=500, detail="Ошибка при получении бронирования")


    @staticmethod
    async def count_user_booking(session: AsyncSession, user_id: int) -> int:
        logger.info(f"Подсчет активных бронирований для пользователя ID: {user_id}")

        try:
            current_msk_time = datetime.now(MSK)
            logger.debug(f"Текущая дата для фильтрации (MSK): {current_msk_time}")
            query = select(func.count()).where(
                and_(
                    user_id == Booking.user_id,
                    Booking.booking_datetime >= datetime.now(),
                    Booking.status == "confirmed",
                )
            )

            logger.debug(f"SQL запрос: {query}")
            result = await session.execute(query)
            count = result.scalar_one_or_none() or 0

            logger.info(f"Найдено {count} активных бронирований для пользователя ID {user_id}")

            if count > 0:
                logger.debug(f"Получение всех броней пользователя для отладки")
                debug_query = select(Booking).where(
                    user_id == Booking.user_id,
                    func.date(Booking.booking_datetime) >= current_msk_time
                )
                debug_result = await session.execute(debug_query)
                debug_bookings = debug_result.scalars().all()

                for booking in debug_bookings:
                    logger.debug(f"Бронь ID: {booking.id}, "
                                 f"Дата: {booking.booking_datetime}, "
                                 f"Статус: {booking.status}, "
                                 f"Услуга: {booking.service_id}")

            return count

        except Exception as e:
            logger.error(f"💥 Ошибка при подсчете бронирований: {str(e)}")
            logger.exception("Полная трассировка ошибки:")
            return 0


    @staticmethod
    async def get_user_bookings(session: AsyncSession, telegram_id: int) -> List[BookingModel]:
        logger.info(f"Получение бронирований пользователя Telegram ID {telegram_id}")
        try:
            user = await UserService.get_user_by_telegram_id(session, telegram_id)
            if not user:
                logger.warning(f"❌ Пользователь с Telegram ID {telegram_id} не найден")
                raise HTTPException(status_code=404, detail="Пользователь не найден")
            current_msk_time = datetime.now(MSK)
            logger.debug(f"Найден пользователь: ID {user.id}, Telegram ID {user.telegram_id}")
            query = select(Booking).where(
                Booking.user_id == user.id,
                "confirmed" == Booking.status,
                Booking.booking_datetime >= current_msk_time
            ).options(
                joinedload(Booking.service),
                joinedload(Booking.specialist)
            )
            result = await session.execute(query)
            bookings = result.scalars().all()
            logger.info(f"Найдено {len(bookings)} активных бронирований для Telegram ID {telegram_id}")
            for booking in bookings:
                logger.debug(f"   - Бронь ID: {booking.id}, Дата: {booking.booking_datetime.astimezone(MSK)}, "
                             f"Услуга: {booking.service_id if booking.service else 'N/A'}")
            return [BookingModel.model_validate(booking) for booking in bookings]
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ошибка при получении бронирований пользователя: {str(e)}")
            raise HTTPException(status_code=500, detail="Ошибка при получении бронирований пользователя")

    @staticmethod
    async def cancel_booking(booking_id: int) -> bool:
        async with async_session_maker() as session:
            try:
                booking = await BookingService.get_booking(session, booking_id)

                if not booking:
                    logger.warning(f"Бронь ID {booking_id} не найдена")
                    return False

                if booking.is_cancelled:
                    logger.info(f"Бронь ID {booking_id} уже отменена")
                    return True

                await ReminderService.cancel_reminders_for_booking(session, booking.id)

                booking.is_cancelled = True
                booking.status = "cancelled"

                session.add(booking)
                await session.commit()

                logger.info(f"Бронь {booking_id} успешно отменена.")
                return True

            except Exception as e:
                logger.error(f"Ошибка при отмене брони {booking_id}: {str(e)}")
                await session.rollback()
                raise HTTPException(status_code=500, detail="Ошибка при отмене брони")