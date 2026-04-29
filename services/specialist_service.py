from typing import List
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from loguru import logger
from sqlalchemy.orm import joinedload

from api.dao import SpecialistDAO, ServiceDAO
from api.schemas import (
    SpecialistCreate,
    SpecialistServiceCreate,
    BookingModel,
    SpecialistModel,
    SpecialistServiceModel,
    ServiceModel, SpecialistUpdate)
from database.models import Service, SpecialistService, Booking, Specialist


class SpecialistServiceClass:
    @staticmethod
    async def create_specialist(session: AsyncSession,
                                specialist_data: SpecialistCreate
                                ) -> SpecialistModel:
        logger.info(f"Создание специалиста: {specialist_data.model_dump()}")
        try:
            new_specialist = await SpecialistDAO.add(session=session, values=specialist_data, commit=True)
            result = await session.execute(
                select(Specialist)
                .options(
                    joinedload(Specialist.service_links).joinedload(SpecialistService.service),
                    joinedload(Specialist.bookings),
                    joinedload(Specialist.schedules)
                )
                .where(new_specialist.id == Specialist.id)
            )
            new_specialist = result.scalars().first()
            return SpecialistModel.model_validate(new_specialist)
        except Exception as e:
            logger.error(f"Ошибка при создании специалиста: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail="Ошибка при создании специалиста")

    @staticmethod
    async def add_service_to_specialist(
            session: AsyncSession,
            specialist_service: SpecialistServiceCreate
    ) -> SpecialistServiceModel:
        logger.info(
            f"Добавление услуги ID {specialist_service.service_id} специалисту ID {specialist_service.specialist_id}")
        try:
            # ищем специалиста
            specialist = await SpecialistDAO.find_one_or_none_by_id(session=session,
                                                                    data_id=specialist_service.specialist_id)
            if not specialist:
                raise HTTPException(status_code=404, detail="Специалист не найден")
            # ищем услугу
            service = await ServiceDAO.find_one_or_none_by_id(session=session, data_id=specialist_service.service_id)
            if not service:
                raise HTTPException(status_code=404, detail="Услуга не найдена")

            existing_link = await session.execute(
                select(SpecialistService).where(
                    and_(
                        SpecialistService.specialist_id == specialist_service.specialist_id,
                        SpecialistService.service_id == specialist_service.service_id
                    )
                )
            )
            if existing_link.scalar_one_or_none():
                raise HTTPException(
                    status_code=400,
                    detail="Эта услуга уже назначена данному специалисту"
                )

            link = SpecialistService(
                specialist_id=specialist_service.specialist_id,
                service_id=specialist_service.service_id
            )
            session.add(link)
            await session.commit()
            result = await session.execute(
                select(SpecialistService)
                .options(
                    joinedload(SpecialistService.specialist),
                    joinedload(SpecialistService.service)
                )
                .where(
                    and_(
                        SpecialistService.specialist_id == specialist_service.specialist_id,
                        SpecialistService.service_id == specialist_service.service_id
                    )
                )
            )
            link = result.scalars().first()
            logger.info(f"Услуга ID {specialist_service.service_id} "
                        f"успешно добавлена мастеру {specialist_service.specialist_id}")
            return SpecialistServiceModel.model_validate(link)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ошибка при добавлении услуги специалисту: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail="Ошибка при добавлении услуги специалисту")

    @staticmethod
    async def get_specialist_services(session: AsyncSession, specialist_id: int) -> List[ServiceModel]:
        logger.info(f"Получение услуг специалиста ID {specialist_id}")
        try:
            specialist = await SpecialistDAO.find_one_or_none_by_id(session=session, data_id=specialist_id)
            if not specialist:
                raise HTTPException(status_code=404, detail="Специалист не найден")

            result = await session.execute(
                select(Service)
                .join(SpecialistService)
                .where(specialist_id == SpecialistService.specialist_id)
            )

            services = result.scalars().all()
            response = [ServiceModel.model_validate(service) for service in services]
            logger.info(f"Для специалиста с ID {specialist_id} найдены услуги: {len(response)}")
            return response
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ошибка при получении услуг специалиста: {str(e)}")
            raise HTTPException(status_code=500, detail="Ошибка при получении услуг специалиста")

    @staticmethod
    async def get_specialist_bookings(session: AsyncSession, specialist_id: int) -> List[BookingModel]:
        logger.info(f"Получение бронирований мастера ID {specialist_id}")
        try:
            specialist = await SpecialistDAO.find_one_or_none_by_id(session=session, data_id=specialist_id)
            if not specialist:
                raise HTTPException(status_code=404, detail="Специалист не найден")

            result = await session.execute(
                select(Booking)
                .where(specialist_id == Booking.specialist_id)
                .options(joinedload(Booking.specialist),
                         joinedload(Booking.service),
                         joinedload(Booking.user)
                         )
            )

            bookings = result.scalars().all()
            return [BookingModel.model_validate(booking) for booking in bookings]
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ошибка при получении бронирований специалиста: {str(e)}")
            raise HTTPException(status_code=500, detail="Ошибка при получении бронирований специалиста")

    @staticmethod
    async def get_specialists(session: AsyncSession) -> List[SpecialistModel]:
        logger.info("Получение списка специалистов")
        result = await SpecialistDAO.find_all(session=session)
        return [SpecialistModel.model_validate(res) for res in result]

    @staticmethod
    async def get_specialist(session: AsyncSession, specialist_id: int) -> SpecialistModel:
        logger.info(f"Получение специалиста ID {specialist_id}")
        try:
            result = await session.execute(
                select(Specialist)
                .where(specialist_id == Specialist.id)
            )
            specialist = result.scalars().first()

            if not specialist:
                raise HTTPException(status_code=404, detail="Специалист не найден")
            logger.info(f"Специалист ID {specialist_id} найден")
            return SpecialistModel.model_validate(specialist)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ошибка при получении специалиста: {str(e)}")
            raise HTTPException(status_code=500, detail="Ошибка при получении специалиста")


    @staticmethod
    async def update_specialist(session: AsyncSession, specialist_id: int,
                                specialist_data: SpecialistUpdate) -> SpecialistModel:
        logger.info(f"Обновление данных специалиста {specialist_id} : {specialist_data.model_dump()}")
        try:
            updated_specialist = await SpecialistDAO.update(
                session=session,
                filters={"id": specialist_id},
                values=specialist_data.model_dump(exclude_unset=True),
                commit=True,
                load_options=[
                    joinedload(Specialist.service_links).joinedload(SpecialistService.service),
                    joinedload(Specialist.bookings),
                    joinedload(Specialist.schedules)
                ]
            )
            if not updated_specialist:
                raise HTTPException(status_code=404, detail="Специалист не найден")

            return_updated_specialist = await SpecialistServiceClass.get_specialist(
                session = session,
                specialist_id=specialist_id)
            return SpecialistModel.model_validate(return_updated_specialist)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ошибка при обновлении специалиста: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail="Ошибка при обновлении специалиста")