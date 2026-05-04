from datetime import date, datetime, timezone, timedelta
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
                await BookingService.schedule_reminders(session=session, booking=new_booking)
            except Exception as reminder_error:
                logger.warning(f'Ошибка при планировании напоминаний: {str(reminder_error)}')

            return booking_result

        except Exception as e:
            await session.rollback()
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(status_code=500, detail="Ошибка при создании бронирования")


    @staticmethod
    async def schedule_reminders(session: AsyncSession, booking: Booking):
        try:
            from celery_app import app

            reminder_config = [
                (24, 'reminder_24h_task_id'),
                (6, 'reminder_6h_task_id'),
                (1, 'reminder_1h_task_id')
            ]

            booking_id = booking.id
            booking_dt = booking.booking_datetime

            if booking_dt.tzinfo is None:
                booking_dt = booking_dt.replace(tzinfo=timezone.utc)

            current_time_utc = datetime.now(timezone.utc)

            logger.info(f"Планирование напоминаний для брони {booking_id}: {booking_dt.astimezone(MSK)} (MSK)")

            task_updates = {}

            for hours_before, task_id_field in reminder_config:
                eta_utc = booking_dt - timedelta(hours=hours_before)

                if eta_utc <= current_time_utc:
                    logger.warning(f"Напоминание за {hours_before}ч для брони {booking_id} пропущено")
                    task_updates[task_id_field] = None
                    continue

                task_id = f"reminder_{booking_id}_{hours_before}h"
                # проверка на наличие задачи перед тем как создать новую (избавление от дубликатов)
                try:
                    existing_task = app.AsyncResult(task_id)
                    if existing_task.state in ['PENDING', 'RETRY', 'STARTED']:
                        logger.info(f"Задача {task_id} уже существует (статус: {existing_task.state})")
                        task_updates[task_id_field] = task_id
                        continue
                except Exception as check_error:
                    logger.debug(f"Не удалось проверить задачу {task_id}: {check_error}")

                task = app.send_task(
                    'services.tasks_service.send_reminder',
                    args=(booking_id, hours_before),
                    eta=eta_utc,
                    task_id=task_id
                )
                task_updates[task_id_field] = task.id
                logger.info(f"Запланировано напоминание за {hours_before}ч: task_id={task.id}")

            # Обновляем booking в отдельной операции
            for field, value in task_updates.items():
                setattr(booking, field, value)

            await session.commit()
            logger.info(f"Напоминания для брони {booking_id} сохранены")

        except Exception as e:
            logger.error(f"Ошибка при планировании напоминаний: {str(e)}")
            await session.rollback()
            raise


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
        from celery_app import app
        async with async_session_maker() as session:
            try:
                booking = await BookingService.get_booking(session, booking_id)

                if not booking:
                    logger.warning(f"Бронь ID {booking_id} не найдена")
                    return False

                if booking.is_cancelled:
                    logger.info(f"Бронь ID {booking_id} уже отменена")
                    return True

                # Отменяем Celery задачи
                task_ids = [
                    (booking.reminder_24h_task_id, '24h'),
                    (booking.reminder_6h_task_id, '6h'),
                    (booking.reminder_1h_task_id, '1h')
                ]

                revoked_count = 0
                for task_id, reminder_type in task_ids:
                    if task_id:
                        try:
                            # Проверяем существует ли задача перед отменой
                            task_result = app.AsyncResult(task_id)
                            if task_result.state in ['PENDING', 'RETRY']:
                                app.control.revoke(task_id, terminate=True, signal='SIGTERM')
                                logger.info(f"Отменена задача {reminder_type} напоминания: {task_id}")
                                revoked_count += 1
                            else:
                                logger.debug(
                                    f"Задача {task_id} уже выполнена или не существует, статус: {task_result.state}")
                        except Exception as revoke_error:
                            logger.error(f"Ошибка при отмене задачи {task_id}: {revoke_error}")

                # Обновляем статус брони
                booking.status = "cancelled"
                booking.is_cancelled = True

                # Очищаем task_id отмененных напоминаний
                booking.reminder_24h_task_id = None
                booking.reminder_6h_task_id = None
                booking.reminder_1h_task_id = None

                session.add(booking)
                await session.commit()

                logger.info(f"Бронь {booking_id} успешно отменена. Отменено задач: {revoked_count}")
                return True

            except Exception as e:
                logger.error(f"Ошибка при отмене брони {booking_id}: {str(e)}")
                await session.rollback()
                raise HTTPException(status_code=500, detail="Ошибка при отмене брони")