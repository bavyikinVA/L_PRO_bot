import pytz
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.dao import ScheduleDAO
from api.schemas import (
    SpecialistCreate,
    ServiceCreate,
    SpecialistServiceCreate,
    ServiceUpdate, SpecialistModel, ServiceModel, BookingModel, SpecialistScheduleModel, SpecialistUpdate)
from database.database import db

from services.booking_service import BookingService
from services.schedule_service import ScheduleService
from services.service_service import ServiceService
from services.specialist_service import SpecialistServiceClass
from services.user_service import UserService

MOSCOW_TZ = pytz.timezone("Europe/Moscow")

api_router = APIRouter(prefix="/api")


# Service Endpoints
@api_router.post("/services",
                 summary="Добавить услугу",
                 tags=["Service Endpoints"])
async def create_new_service(
        service_data: ServiceCreate,
        session: AsyncSession = Depends(db.get_db_with_commit)) -> ServiceModel:
    return await ServiceService.create_service(session, service_data)


@api_router.patch("/services/{service_id}",
                  summary="Обновить услугу",
                  tags=["Service Endpoints"])
async def update_service(
        service_id: int,
        service_data: ServiceUpdate,
        session: AsyncSession = Depends(db.get_db_with_commit)) -> ServiceModel:
    return await ServiceService.update_service(session, service_id, service_data)


@api_router.get("/services",
                summary="Получить список услуг",
                tags=["Service Endpoints"])
async def get_services(session: AsyncSession = Depends(db.get_db)) -> List[ServiceModel]:
    return await ServiceService.get_services(session)


@api_router.get("/services/{service_id}",
                summary="Получить услугу по id",
                tags=["Service Endpoints"])
async def get_service(
        service_id: int,
        session: AsyncSession = Depends(db.get_db)):
    return await ServiceService.get_service(session, service_id)


@api_router.get("/services/{service_id}/specialists",
                summary="Получить специалистов услуги",
                tags=["Service Endpoints"])
async def get_service_specialists(
        service_id: int,
        session: AsyncSession = Depends(db.get_db)):
    return await ServiceService.get_service_specialists(session, service_id)


# Specialist Endpoints
@api_router.get("/specialists",
                summary="Получить список специалистов",
                tags=["Specialist Endpoints"])
async def get_specialists(session: AsyncSession = Depends(db.get_db)) -> List[SpecialistModel]:
    return await SpecialistServiceClass.get_specialists(session)


@api_router.get("/specialists/{specialist_id}",
                summary="Получить специалиста по ID",
                tags=["Specialist Endpoints"])
async def get_specialist(specialist_id: int, session: AsyncSession = Depends(db.get_db)):
    return await SpecialistServiceClass.get_specialist(session, specialist_id)


@api_router.post("/specialists",
                 summary="Добавить специалиста",
                 tags=["Specialist Endpoints"])
async def create_specialist(
        specialist_data: SpecialistCreate,
        session: AsyncSession = Depends(db.get_db_with_commit)) -> SpecialistModel:
    return await SpecialistServiceClass.create_specialist(session, specialist_data)


@api_router.post("/specialists/{specialist_id}/services",
                 summary="Добавить услугу специалисту",
                 tags=["Specialist Endpoints"])
async def add_service_to_specialist(
        specialist_service: SpecialistServiceCreate,
        session: AsyncSession = Depends(db.get_db_with_commit)):
    return await SpecialistServiceClass.add_service_to_specialist(session, specialist_service)


@api_router.get("/specialists/{specialist_id}/services",
                summary="Получить услуги специалиста",
                tags=["Specialist Endpoints"])
async def get_specialist_services(
        specialist_id: int,
        session: AsyncSession = Depends(db.get_db)):
    return await SpecialistServiceClass.get_specialist_services(session, specialist_id)


@api_router.patch("/specialists/{specialist_id}",
                  summary="Обновить данные специалиста",
                  tags=["Specialist Endpoints"])
async def update_specialist(specialist_id: int,
                            specialist_data: SpecialistUpdate,
                            session: AsyncSession = Depends(db.get_db_with_commit)
                            ) -> SpecialistModel:
    return await SpecialistServiceClass.update_specialist(session, specialist_id, specialist_data)


@api_router.get("/specialists/{specialist_id}/slots",
                summary="Получить слоты специалиста",
                tags=['Specialist Endpoints'])
async def get_available_slots(
    specialist_id: int,
    start_date: date,
    service_id: Optional[int] = None,
    session: AsyncSession = Depends(db.get_db)
):
    return await BookingService.get_available_slots(session, specialist_id, start_date, service_id)


# Booking Endpoints
@api_router.post("/bookings", summary="Создать новую запись", tags=["Booking Endpoints"])
async def create_booking(booking_data: BookingModel, session: AsyncSession = Depends(db.get_db_with_commit)):
    return await BookingService.create_booking(session, booking_data)


@api_router.get("/bookings/{telegram_id}", summary="Получить бронирования пользователя", tags=["Booking Endpoints"])
async def get_bookings(
        telegram_id: int,
        session: AsyncSession = Depends(db.get_db)
) -> List[BookingModel]:
    return await BookingService.get_user_bookings(session, telegram_id)


@api_router.delete("/bookings/{booking_id}", summary="Отменить бронирование", tags=["Booking Endpoints"])
async def cancel_booking_endpoint(booking_id: int) -> dict:
    success = await BookingService.cancel_booking(booking_id)
    if success:
        return {"message": "Бронирование успешно отменено"}
    raise HTTPException(status_code=404, detail="Бронирование не найдено или уже отменено")


# Schedule Endpoints
@api_router.post("/schedules", summary="Добавить расписание", tags=["Schedule Endpoints"])
async def create_schedule(
        schedule_data: SpecialistScheduleModel,
        session: AsyncSession = Depends(db.get_db_with_commit)
) -> SpecialistScheduleModel:
    return await ScheduleService.create_schedule(session, schedule_data)


@api_router.patch("/schedules/{schedule_id}", summary="Обновить расписание", tags=["Schedule Endpoints"])
async def update_schedule(
        schedule_id: int,
        schedule_data: SpecialistScheduleModel,
        session: AsyncSession = Depends(db.get_db_with_commit)
) -> SpecialistScheduleModel:
    return await ScheduleService.update_schedule(session, schedule_id, schedule_data)


@api_router.get("/schedules/{schedule_id}", summary="Получить расписание", tags=["Schedule Endpoints"])
async def get_schedule(
        schedule_id: int,
        session: AsyncSession = Depends(db.get_db)
) -> SpecialistScheduleModel:
    return await ScheduleService.get_schedule(session, schedule_id)


@api_router.get("/specialists/{specialist_id}/schedules", summary="Получить расписания специалиста",
                tags=["Schedule Endpoints"])
async def get_specialist_schedules(
        specialist_id: int,
        session: AsyncSession = Depends(db.get_db)
) -> List[SpecialistScheduleModel]:
    return await ScheduleService.get_specialist_schedules(session, specialist_id)


@api_router.delete("/schedules/{specialist_id}",
                   summary="Очистить расписание специалиста", tags=["Schedule Endpoints"])
async def delete_specialist_schedule(specialist_id: int,
                                     session: AsyncSession = Depends(db.get_db_with_commit)):
    return await ScheduleDAO.clear_existing_schedule(session, specialist_id)


@api_router.get("/user/{telegram_id}",
                summary="Получить id пользователя по TG_id",
                tags=["User Endpoints"])
async def get_user(telegram_id: int, session: AsyncSession = Depends(db.get_db)) -> int:
    user = await (UserService.get_user_by_telegram_id(session, telegram_id))
    return user.id