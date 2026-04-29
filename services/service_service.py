from typing import List
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from sqlalchemy.orm import joinedload

from api.dao import ServiceDAO
from api.schemas import ServiceCreate, ServiceUpdate, ServiceModel, SpecialistModel
from database.models import Service, SpecialistService, Specialist


class ServiceService:
    @staticmethod
    async def create_service(session: AsyncSession, service_data:ServiceCreate) -> ServiceModel:
        logger.info(f"Создание услуги {service_data.model_dump()}")
        try:
            new_service = await ServiceDAO.add(session=session,
                                               values=service_data,
                                               commit=True)
            return ServiceModel.model_validate(new_service)
        except Exception as e:
            logger.error(f"Ошибка при создании услуги: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail="Ошибка при создании услуги")


    @staticmethod
    async def update_service(session:AsyncSession,
                             service_id: int,
                             update_data: ServiceUpdate) -> ServiceModel:
        logger.info(f"Обновление услуги ID {service_id}")
        try:
            updated_service = await ServiceDAO.update(session=session,
                                                   filters={"id":service_id},
                                                   values=update_data.model_dump(exclude_unset=True),
                                                   commit=True,
                                                   load_options=[
                                                       joinedload(Service.specialist_links)
                                                   .joinedload(SpecialistService.specialist),
                                                       joinedload(Service.bookings)]
            )
            if not updated_service:
                raise HTTPException(status_code=404, detail="Услуга не найдена")
            return ServiceModel.model_validate(updated_service)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ошибка при обновлении услуги: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail="Ошибка при обновлении услуги")


    @staticmethod
    async def get_services(session: AsyncSession) -> List[ServiceModel]:
        logger.info("Получение списка услуг")
        result = await ServiceDAO.find_all(session=session)
        services = [ServiceModel.model_validate(res) for res in result]
        services.sort(key=lambda x: x.id)
        return services


    @staticmethod
    async def get_service(session: AsyncSession, service_id: int) -> ServiceModel:
        logger.info(f"Получение услуги ID {service_id}")
        try:
            result = await session.execute(
                select(Service)
                .options(
                    joinedload(Service.specialist_links).joinedload(SpecialistService.specialist),
                    joinedload(Service.bookings)
                )
                .where(service_id == Service.id)
            )
            service = result.scalars().first()
            if not service:
                raise HTTPException(status_code=404, detail="Услуга не найдена")
            return ServiceModel.model_validate(service)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ошибка при получении услуги: {str(e)}")
            raise HTTPException(status_code=500, detail="Ошибка при получении услуги")

    @staticmethod
    async def get_service_specialists(session: AsyncSession, service_id: int) -> List[SpecialistModel]:
        logger.info(f"Получение специалистов для услуги ID {service_id}")
        try:
            service = await ServiceDAO.find_one_or_none_by_id(session=session, data_id=service_id)
            if not service:
                raise HTTPException(status_code=404, detail="Услуга не найдена")

            result = await session.execute(
                select(Specialist)
                .join(SpecialistService, Specialist.id == SpecialistService.specialist_id)
                .join(Service, Service.id == SpecialistService.service_id)
                .where(service_id == Service.id)
            )
            specialists = result.scalars().all()

            return [SpecialistModel.model_validate(specialist) for specialist in specialists]

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ошибка при получении специалистов услуги: {str(e)}")
            raise HTTPException(status_code=500, detail="Ошибка при получении специалистов услуги")