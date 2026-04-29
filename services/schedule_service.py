from typing import List
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from loguru import logger

from api.dao import ScheduleDAO, SpecialistDAO
from api.schemas import SpecialistScheduleModel
from database.models import Schedule


class ScheduleService:
    @staticmethod
    async def create_schedule(session: AsyncSession, schedule_data: SpecialistScheduleModel) -> SpecialistScheduleModel:
        logger.info(f"Создание расписания: {schedule_data.model_dump()}")
        try:
            specialist = await SpecialistDAO.find_one_or_none_by_id(session=session,
                                                                    data_id=schedule_data.specialist_id)
            if not specialist:
                raise HTTPException(status_code=404, detail="Специалист не найден")
            new_schedule = await ScheduleDAO.add(session=session, values=schedule_data, commit=True)
            result = await session.execute(
                select(Schedule)
                .options(joinedload(Schedule.specialist))
                .where(new_schedule.id == Schedule.id)
            )
            new_schedule = result.scalars().first()
            return SpecialistScheduleModel.model_validate(new_schedule)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ошибка при создании расписания: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail="Ошибка при создании расписания")


    @staticmethod
    async def get_schedule(session: AsyncSession, schedule_id: int) -> SpecialistScheduleModel:
        logger.info(f"Получение расписания ID {schedule_id}")
        try:
            result = await session.execute(
                select(Schedule)
                .options(joinedload(Schedule.specialist))
                .where(schedule_id == Schedule.id)
            )
            schedule = result.scalars().first()
            if not schedule:
                raise HTTPException(status_code=404, detail="Расписание не найдено")
            return SpecialistScheduleModel.model_validate(schedule)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ошибка при получении расписания: {str(e)}")
            raise HTTPException(status_code=500, detail="Ошибка при получении расписания")


    @staticmethod
    async def get_specialist_schedules(session: AsyncSession, specialist_id: int) -> List[SpecialistScheduleModel]:
        logger.info(f"Получение расписаний специалиста ID {specialist_id}")
        try:
            specialist = await SpecialistDAO.find_one_or_none_by_id(session=session, data_id=specialist_id)
            if not specialist:
                raise HTTPException(status_code=404, detail="Специалист не найден")
            result = await session.execute(
                select(Schedule)
                .where(specialist_id == Schedule.specialist_id)
                .options(joinedload(Schedule.specialist))
            )
            schedules = result.scalars().all()
            return [SpecialistScheduleModel.model_validate(schedule) for schedule in schedules]
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ошибка при получении расписаний специалиста: {str(e)}")
            raise HTTPException(status_code=500, detail="Ошибка при получении расписаний специалиста")


    @staticmethod
    async def update_schedule(session: AsyncSession,
                              schedule_id: int,
                              schedule_data: SpecialistScheduleModel) -> SpecialistScheduleModel:
        logger.info(f"Обновление расписания ID {schedule_id}: {schedule_data.model_dump()}")
        try:
            schedule = await ScheduleDAO.find_one_or_none_by_id(session=session, data_id=schedule_id)
            if not schedule:
                raise HTTPException(status_code=404, detail="Расписание не найдено")
            if schedule_data.specialist_id:
                specialist = await SpecialistDAO.find_one_or_none_by_id(session=session,
                                                                        data_id=schedule_data.specialist_id)
                if not specialist:
                    raise HTTPException(status_code=404, detail="Специалист не найден")

            updated_schedule = await ScheduleDAO.update(
                session=session,
                filters={"id":schedule_id},
                values=schedule_data.model_dump(),
                commit=True)

            return SpecialistScheduleModel.model_validate(updated_schedule)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ошибка при обновлении расписания: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail="Ошибка при обновлении расписания")