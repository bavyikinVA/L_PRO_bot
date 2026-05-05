from datetime import date, time
from datetime import datetime
from typing import List
from zoneinfo import ZoneInfo

from sqlalchemy import Integer, ForeignKey, DateTime, String, Boolean, Date, Time, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int | None] = mapped_column(Integer, unique=True, nullable=True, index=True)
    username: Mapped[str | None] = mapped_column(String, nullable=True)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str | None] = mapped_column(String, nullable=True)
    patronymic: Mapped[str | None] = mapped_column(String, nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String, nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    bookings: Mapped[List["Booking"]] = relationship(back_populates="user")


class Service(Base):  # класс процедур/услуг
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str]  # название
    description: Mapped[str] # комментарий
    price: Mapped[int] # стоимость
    duration_minutes: Mapped[int] = mapped_column(Integer, default=120)
    icon: Mapped[str | None] = mapped_column(String, nullable=True)

    # Связь с Specialist
    specialist_links: Mapped[List["SpecialistService"]] = relationship(
        back_populates="service"
    )
    bookings: Mapped[List["Booking"]] = relationship(back_populates="service")


class Specialist(Base):
    __tablename__ = "specialists"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)

    work_experience: Mapped[str] = mapped_column(String, nullable=True)
    photo: Mapped[str] = mapped_column(String, nullable=True)

    service_links: Mapped[List["SpecialistService"]] = relationship(
        back_populates="specialist"
    )

    bookings: Mapped[List["Booking"]] = relationship(back_populates="specialist")
    schedules: Mapped[List["Schedule"]] = relationship(
        back_populates="specialist",
        cascade="all, delete-orphan"
    )


class SpecialistService(Base):
    __tablename__ = "specialist_services"

    specialist_id: Mapped[int] = mapped_column(ForeignKey("specialists.id"), primary_key=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), primary_key=True)

    specialist: Mapped["Specialist"] = relationship(back_populates="service_links")
    service: Mapped["Service"] = relationship(back_populates="specialist_links")


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True)
    specialist_id: Mapped[int] = mapped_column(ForeignKey("specialists.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"))

    booking_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String, default="confirmed")
    duration_minutes: Mapped[int] = mapped_column(Integer, default=120)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo("UTC")))
    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    # Relationships
    specialist: Mapped["Specialist"] = relationship(back_populates="bookings")
    user: Mapped["User"] = relationship(back_populates="bookings")
    service: Mapped["Service"] = relationship(back_populates="bookings")
    # Индексы
    __table_args__ = (
        Index('ix_bookings_specialist_datetime', 'specialist_id', 'booking_datetime'),
        Index('ix_bookings_user_datetime', 'user_id', 'booking_datetime'),
        Index('ix_bookings_cancelled', 'is_cancelled'),
    )


class Schedule(Base):
    __tablename__ = "schedules"
    id: Mapped[int] = mapped_column(primary_key=True)
    specialist_id: Mapped[int] = mapped_column(ForeignKey("specialists.id"))
    work_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    is_working: Mapped[bool] = mapped_column(Boolean, default=True)
    slot_duration_minutes: Mapped[int] = mapped_column(Integer, default=120)
    # Relationships
    specialist: Mapped["Specialist"] = relationship(
        back_populates="schedules",
        lazy='select'
    )
    __table_args__ = (
        UniqueConstraint("specialist_id", "work_date", name="uq_schedule_specialist_date"),
    )

class BookingReminder(Base):
    __tablename__ = "booking_reminders"

    id: Mapped[int] = mapped_column(primary_key=True)

    booking_id: Mapped[int] = mapped_column(
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    hours_before: Mapped[int] = mapped_column(Integer, nullable=False)
    remind_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    status: Mapped[str] = mapped_column(String, default="pending", nullable=False, index=True)
    task_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)

    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(ZoneInfo("UTC")),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint("booking_id", "hours_before", name="uq_booking_reminder_once"),
        Index("ix_booking_reminders_status_remind_at", "status", "remind_at"),
    )
