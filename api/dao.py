from calendar import monthrange
from datetime import date, timedelta, datetime, time, timezone
from typing import List, Optional, Any
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from loguru import logger
from sqlalchemy import select, and_, func, or_, extract, Interval
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database.base import BaseDAO
from api.schemas import BookingModel, UserModel
from database.models import (
    Service, Specialist, SpecialistService,
    Booking, Schedule, User
)

MSK = ZoneInfo("Europe/Moscow")

class UserDAO(BaseDAO[User]):
    model = User

    @classmethod
    async def find_existing_user(
            cls,
            session: AsyncSession,
            first_name: Optional[str] = None,
            last_name: Optional[str] = None,
            phone_number: Optional[str] = None,
            username: Optional[str] = None,
            telegram_id: Optional[int] = None
    ) -> Optional[UserModel]:
        logger.info(
            f"Поиск пользователя по параметрам: first_name={first_name}, last_name={last_name}, "
            f"phone_number={phone_number}, username={username}, telegram_id={telegram_id}")
        query = select(User)
        conditions = []
        if first_name:
            conditions.append(func.lower(User.first_name) == func.lower(first_name))
        if last_name:
            conditions.append(func.lower(User.last_name) == func.lower(last_name))
        if phone_number:
            conditions.append(User.phone_number == phone_number)
        if username:
            conditions.append(func.lower(User.username) == func.lower(username))
        if telegram_id:
            conditions.append(User.telegram_id == telegram_id)
        if conditions:
            query = query.where(or_(*conditions))
        result = await session.execute(query)
        user = result.scalars().first()
        logger.info(f"Пользователь {'найден' if user else 'не найден'} по указанным параметрам")
        if user is None:
            return None
        try:
            user_model = UserModel.model_validate(user)
            logger.debug(f"Validated UserModel: {user_model.model_dump()}")
            return user_model
        except Exception as e:
            logger.error(f"Ошибка валидации UserModel: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Ошибка валидации пользователя: {str(e)}")


class SpecialistDAO(BaseDAO[Specialist]):
    model = Specialist


class ServiceDAO(BaseDAO[Service]):
    model = Service


class SpecialistServiceDAO(BaseDAO[SpecialistService]):
    model = SpecialistService


class BookingDAO(BaseDAO[Booking]):
    model = Booking

    @classmethod
    async def get_user_bookings_with_specialist_info(cls, session: AsyncSession, user_id: int) -> List[BookingModel]:
        logger.info(f"Получение бронирований пользователя с ID: {user_id} с информацией о специалисте")
        try:
            query = (
                select(cls.model)
                .options(
                    joinedload(cls.model.specialist),
                    joinedload(cls.model.service),
                    joinedload(cls.model.user)
                )
                .where(user_id == cls.model.user_id)
                .order_by(cls.model.booking_datetime))

            result = await session.execute(query)
            bookings = result.unique().scalars().all()
            booking_models = [BookingModel.model_validate(booking) for booking in bookings]
            logger.info(f"Найдено {len(booking_models)} бронирований для пользователя ID {user_id}")
            return booking_models
        except Exception as e:
            logger.error(f"Ошибка при получении бронирований: {str(e)}")
            raise HTTPException(status_code=500, detail="Ошибка при получении бронирований")


    @classmethod
    async def get_available_slots(
            cls,
            session: AsyncSession,
            specialist_id: int,
            start_date: date,
            service_id: Optional[int]
    ) -> dict[str, Any]:
        try:
            start_of_week = start_date - timedelta(days=start_date.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            logger.info(
                f"Получение доступных слотов для специалиста ID {specialist_id} с {start_of_week} по {end_of_week}")
            # Получение расписания специалиста
            schedule_dao = ScheduleDAO()
            specialist_schedule = await schedule_dao.get_schedule_for_period(
                session, specialist_id, start_of_week, end_of_week)

            # Получение существующих броней
            query = select(cls.model).where(
                and_(
                    cls.model.specialist_id == specialist_id,
                    cls.model.booking_datetime >= datetime.combine(start_of_week, time.min, tzinfo=timezone.utc),
                    cls.model.booking_datetime <= datetime.combine(end_of_week, time.max, tzinfo=timezone.utc)
                )
            )
            result = await session.execute(query)
            existing_bookings = result.scalars().all()
            duration_minutes = 120  # Длительность по умолчанию
            if service_id:
                service = await ServiceDAO.find_one_or_none_by_id(session=session, data_id=service_id)
                if service:
                    duration_minutes = service.duration_minutes
                else:
                    logger.warning(f"Услуга ID {service_id} не найдена, используется длительность по умолчанию")

            # Словарь расписания по датам
            schedule_by_date = {s.work_date: s for s in specialist_schedule}

            # Множество занятых слотов
            booked_slots = set()
            for booking in existing_bookings:
                booking_start = booking.booking_datetime.astimezone(MSK)
                booking_end = booking_start + timedelta(minutes=booking.duration_minutes)
                current = booking_start
                while current < booking_end:
                    booked_slots.add((current.date(), current.time()))
                    current += timedelta(minutes=15)  # Шаг для проверки пересечений

            week_days_rus = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

            available_slots = []
            for day_offset in range(7):
                current_date = start_of_week + timedelta(days=day_offset)
                day_name_rus = week_days_rus[day_offset]
                logger.info(f"Обработка day_offset={day_offset}, current_date={current_date}")
                day_schedule = schedule_by_date.get(current_date)
                day_slots = []
                if current_date >= datetime.now(MSK).date() and day_schedule and day_schedule.is_working:
                    # Генерируем слоты согласно расписанию
                    slot_duration = day_schedule.slot_duration_minutes or duration_minutes
                    working_hours = cls.generate_time_slots(
                        day_schedule.start_time,
                        day_schedule.end_time,
                        slot_duration
                    )

                    for slot_time in working_hours:
                        slot_start = datetime.combine(current_date, slot_time).replace(tzinfo=MSK)
                        slot_end = slot_start + timedelta(minutes=slot_duration)
                        if slot_end.time() > day_schedule.end_time:
                            continue
                        is_available = True
                        for booking in existing_bookings:
                            booking_start = booking.booking_datetime.astimezone(MSK)
                            booking_end = booking_start + timedelta(minutes=booking.duration_minutes)

                            # Проверяем пересечение интервалов
                            if not (slot_end <= booking_start or slot_start >= booking_end):
                                is_available = False
                                break

                        if slot_start < datetime.now(MSK):
                            is_available = False

                        if is_available:
                            day_slots.append(slot_time.strftime("%H:%M"))

                available_slots.append({
                    "day": day_name_rus,
                    "date": current_date.isoformat(),
                    "slots": day_slots,
                    "total_slots": len(day_slots)
                })

            response = {
                "days": available_slots,
                "total_week_slots": sum(day["total_slots"] for day in available_slots)
            }
            logger.info(f"Найдено {response['total_week_slots']} доступных слотов для специалиста ID {specialist_id}")
            return response

        except Exception as e:
            logger.error(f"Ошибка в api/dao/get_available_slots: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Ошибка при получении доступных слотов"
            )


    @classmethod
    def generate_time_slots(cls, start_time: time, end_time: time, interval_minutes: int) -> List[time]:
        slots = []
        current_dt = datetime.combine(date.today(), start_time)
        end_dt = datetime.combine(date.today(), end_time)
        while current_dt < end_dt:
            slots.append(current_dt.time())
            current_dt += timedelta(minutes=interval_minutes)
        return slots


    @classmethod
    async def book_appointment(
            cls,
            session: AsyncSession,
            specialist_id: int,
            user_id: int,
            service_id: int,
            booking_datetime: datetime,
            commit: bool = True
    ) -> Booking:
        try:
            logger.info(f"Создание брони для специалиста ID {specialist_id}, пользователя ID {user_id}, "
                        f"услуги ID {service_id} на {booking_datetime}")

            if booking_datetime.tzinfo is None:
                booking_datetime = booking_datetime.replace(tzinfo=timezone.utc)
                logger.debug(f"Время брони без tzinfo, установлено UTC: {booking_datetime}")

            # Проверка, что время бронирования в будущем (в UTC)
            current_time_utc = datetime.now(timezone.utc)
            if booking_datetime < current_time_utc:
                raise HTTPException(
                    status_code=400,
                    detail="Дата и время бронирования не могут быть меньше текущего времени"
                )

            # Проверка, что слот находится в рабочем расписании
            schedule_dao = ScheduleDAO()
            schedule = await schedule_dao.get_schedule_for_period(
                session=session,
                specialist_id=specialist_id,
                start_date=booking_datetime.date(),
                end_date=booking_datetime.date()
            )
            if not schedule or not schedule[0].is_working:
                raise HTTPException(status_code=400, detail="Специалист не работает в указанный день")

            schedule = schedule[0]
            booking_time = booking_datetime.astimezone(MSK).time()
            if not (schedule.start_time <= booking_time <= schedule.end_time):
                raise HTTPException(status_code=400, detail="Время бронирования вне рабочего расписания")

            service = await ServiceDAO.find_one_or_none_by_id(session=session, data_id=service_id)
            if not service:
                raise HTTPException(status_code=404, detail="Услуга не найдена")

            duration_minutes = service.duration_minutes

            # Проверка, что слот не занят
            booking_end = booking_datetime + timedelta(minutes=duration_minutes)
            query = select(cls.model).where(
                and_(
                    cls.model.specialist_id == specialist_id,
                    cls.model.is_cancelled == False,
                    cls.model.booking_datetime < booking_end,
                    cls.model.booking_datetime + func.cast(
                        func.concat(cls.model.duration_minutes, ' minutes'),
                        Interval) > booking_datetime
                )
            )
            result = await session.execute(query)
            if result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Слот уже забронирован")

            # Создание новой брони
            new_booking = cls.model(
                specialist_id=specialist_id,
                user_id=user_id,
                service_id=service_id,
                booking_datetime=booking_datetime,
                duration_minutes=duration_minutes,
                status="confirmed",
                created_at=datetime.now(timezone.utc),
                is_cancelled=False
            )
            session.add(new_booking)
            if commit:
                await session.commit()
                await session.refresh(new_booking)
                result = await session.execute(
                    select(cls.model)
                    .options(
                        joinedload(cls.model.specialist),
                        joinedload(cls.model.service),
                        joinedload(cls.model.user)
                    )
                    .where(new_booking.id == cls.model.id)
                )
                new_booking = result.scalars().first()
            logger.info(f"Бронь успешно создана с ID {new_booking.id}")
            return new_booking
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ошибка при создании брони: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail="Ошибка при создании брони")


class ScheduleDAO(BaseDAO[Schedule]):
    model = Schedule

    @classmethod
    async def generate_monthly_schedule(cls,
                                        session: AsyncSession,
                                        specialist_id: int,
                                        working_days: List[str],
                                        start_time: time,
                                        end_time: time,
                                        slot_duration_minutes: int,
                                        target_month: int,
                                        target_year: int,
                                        commit: bool = True) -> List[Schedule]:
        logger.info(f"Генерация расписания для специалиста ID {specialist_id}, рабочие дни: {working_days}, "
                    f"месяц: {target_month}, год: {target_year}.")

        day_mapping = {
            'mon': 0,
            'tue': 1,
            'wed': 2,
            'thu': 3,
            'fri': 4,
            'sat': 5,
            'sun': 6
        }

        if not working_days:
            raise HTTPException(status_code=400, detail="Не указаны рабочие дни")

        if start_time >= end_time:
            raise HTTPException(status_code=400, detail="Время начала должно быть раньше времени окончания")

        selected_weekdays = {day_mapping[day] for day in working_days}
        schedules = []

        # определяем первый и последний день месяца
        first_day = date(target_year, target_month, 1)
        _, last_day = monthrange(year=target_year, month=target_month)
        current_date = first_day
        end_date = date(target_year, target_month, last_day)

        # проверяем существующие записи
        existing_schedules = await cls.get_schedule_for_period(
            session=session, specialist_id=specialist_id,
            start_date=first_day, end_date=end_date)
        existing_dates = {s.work_date for s in existing_schedules}

        while current_date <= end_date:
            if current_date.weekday() in selected_weekdays and current_date not in existing_dates:
                schedule = cls.model(
                    specialist_id=specialist_id,
                    work_date=current_date,
                    start_time=start_time,
                    end_time=end_time,
                    is_working=True,
                    slot_duration_minutes=slot_duration_minutes,
                )
                schedules.append(schedule)
            current_date += timedelta(days=1)
        if schedules:
            session.add_all(schedules)
            try:
                if commit:
                    await session.commit()
                    for schedule in schedules:
                        await session.refresh(schedule)
                logger.info(f"Сгенерировано {len(schedules)} записей расписания для специалиста ID {specialist_id}")
            except Exception as e:
                logger.error(f"Ошибка при генерации расписания: {str(e)}")
                await session.rollback()
                raise
        else:
            logger.info(f"Новые записи расписания не созданы, так как все дни уже существуют")

        return schedules


    @classmethod
    async def update_monthly_schedule(cls,
                                      session: AsyncSession,
                                      specialist_id: int,
                                      working_days: List[str],
                                      start_time: time,
                                      end_time: time,
                                      slot_duration_minutes: int,
                                      target_month: int,
                                      target_year: int,
                                      commit: bool = True) -> List[Schedule]:
        logger.info(f"Обновление расписания для специалиста ID {specialist_id}, "
                    f"месяц: {target_month}, год: {target_year}.")
        day_mapping = {
            'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6
        }
        selected_weekdays = {day_mapping[day] for day in working_days}
        first_day = date(target_year, target_month, 1)
        _, last_day = monthrange(target_year, target_month)
        end_date = date(target_year, target_month, last_day)

        existing_schedules = await cls.get_schedule_for_period(session, specialist_id, first_day, end_date)

        updates = []
        for schedule in existing_schedules:
            if schedule.work_date.weekday() in selected_weekdays:
                schedule.is_working = True
                schedule.start_time = start_time
                schedule.end_time = end_time
                schedule.slot_duration_minutes = slot_duration_minutes
            else:
                schedule.is_working = False

        # добавляем новые записи для дней, которых нет
        existing_dates = {s.work_date for s in existing_schedules}
        current_date = first_day
        while current_date <= end_date:
            if current_date.weekday() in selected_weekdays and current_date not in existing_dates:
                schedule = cls.model(
                    specialist_id=specialist_id,
                    work_date=current_date,
                    start_time=start_time,
                    end_time=end_time,
                    is_working=True,
                    slot_duration_minutes=slot_duration_minutes
                )
                updates.append(schedule)
            current_date += timedelta(days=1)
        if updates:
            session.add_all(updates)
            try:
                if commit:
                    await session.commit()
                    for schedule in updates:
                        await session.refresh(schedule)
                    logger.info(f"Обновлено/добавлено {len(updates)} записей расписания")
            except Exception as e:
                logger.error(f"Ошибка обновления расписания {str(e)}")
                await session.rollback()
                raise
        return updates

    @classmethod
    async def clear_existing_schedule(
            cls,
            session: AsyncSession,
            specialist_id: int,
            month: int = None,
            year: int = None,
            commit: bool = True) -> None:
        logger.info(f"Очистка расписания для специалиста ID {specialist_id}, месяц: {month}, год: {year}")
        today = date.today()
        target_month = month or today.month
        target_year = year or today.year

        query = select(cls.model).where(
            specialist_id == cls.model.specialist_id,
            target_month == extract('month', cls.model.work_date),
            target_year == extract('year', cls.model.work_date)
        )

        result = await session.execute(query)
        existing_schedules = result.scalars().all()

        for schedule in existing_schedules:
            await session.delete(schedule)
        try:
            if commit:
                await session.commit()
            logger.info(f"Удалено {len(existing_schedules)} записей расписания")
        except Exception as e:
            logger.error(f"Ошибка при очистке расписания: {str(e)}")
            await session.rollback()
            raise

    @classmethod
    async def get_schedule_for_period(
            cls,
            session: AsyncSession,
            specialist_id: int,
            start_date: date,
            end_date: date):
        logger.info(f"Получение расписания для специалиста ID {specialist_id} с {start_date} по {end_date}")
        query = select(cls.model).where(
            and_(
                cls.model.specialist_id == specialist_id,
                cls.model.work_date >= start_date,
                cls.model.work_date <= end_date
            )
        ).order_by(cls.model.work_date)

        result = await session.execute(query)
        schedules = result.scalars().all()
        logger.info(f"Найдено {len(schedules)} записей расписания")
        return schedules
