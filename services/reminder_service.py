from datetime import datetime, timezone, timedelta
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from celery_app import app
from database.models import Booking, BookingReminder


class ReminderService:
    REMINDER_HOURS = [24, 6, 1]

    @staticmethod
    async def create_reminders_for_booking(session: AsyncSession, booking: Booking):
        booking_id = booking.id
        booking_dt = booking.booking_datetime

        if booking_dt.tzinfo is None:
            booking_dt = booking_dt.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)

        for hours_before in ReminderService.REMINDER_HOURS:
            remind_at = booking_dt - timedelta(hours=hours_before)

            if remind_at <= now:
                status = "skipped"
            else:
                status = "pending"

            existing_result = await session.execute(
                select(BookingReminder).where(
                    booking_id == BookingReminder.booking_id,
                    hours_before == BookingReminder.hours_before
                )
            )
            existing = existing_result.scalar_one_or_none()

            if existing:
                existing.remind_at = remind_at
                existing.status = status
                existing.error_message = None
                continue

            reminder = BookingReminder(
                booking_id=booking_id,
                hours_before=hours_before,
                remind_at=remind_at,
                status=status
            )
            session.add(reminder)

        await session.commit()

        await ReminderService.schedule_pending_reminders(session, booking_id)

    @staticmethod
    async def schedule_pending_reminders(session: AsyncSession, booking_id: int | None = None):
        now = datetime.now(timezone.utc)

        query = select(BookingReminder).where(
            BookingReminder.status.in_(["pending", "scheduled", "failed"]),
            BookingReminder.remind_at > now
        )

        if booking_id is not None:
            query = query.where(booking_id == BookingReminder.booking_id)

        result = await session.execute(query)
        reminders = result.scalars().all()

        for reminder in reminders:
            task_id = f"booking_reminder_{reminder.id}"

            app.send_task(
                "services.tasks_service.send_reminder",
                args=(reminder.id,),
                eta=reminder.remind_at,
                task_id=task_id
            )

            reminder.task_id = task_id
            reminder.status = "scheduled"

            logger.info(
                f"Запланировано напоминание ID={reminder.id}, "
                f"booking_id={reminder.booking_id}, "
                f"hours_before={reminder.hours_before}, "
                f"task_id={task_id}"
            )

        await session.commit()

    @staticmethod
    async def recover_queue(session: AsyncSession):
        now = datetime.now(timezone.utc)

        result = await session.execute(
            select(BookingReminder).where(
                BookingReminder.status.in_(["pending", "scheduled", "failed"]),
                BookingReminder.remind_at > now
            )
        )

        reminders = result.scalars().all()

        restored = 0

        for reminder in reminders:
            task_id = f"booking_reminder_{reminder.id}"

            app.send_task(
                "services.tasks_service.send_reminder",
                args=(reminder.id,),
                eta=reminder.remind_at,
                task_id=task_id
            )

            reminder.task_id = task_id
            reminder.status = "scheduled"
            reminder.error_message = None
            restored += 1

        await session.commit()

        logger.info(f"Восстановлено напоминаний: {restored}")
        return restored

    @staticmethod
    async def cancel_reminders_for_booking(session: AsyncSession, booking_id: int):
        result = await session.execute(
            select(BookingReminder).where(
                booking_id == BookingReminder.booking_id,
                BookingReminder.status.in_(["pending", "scheduled", "failed"])
            )
        )

        reminders = result.scalars().all()

        for reminder in reminders:
            if reminder.task_id:
                app.control.revoke(reminder.task_id, terminate=False)

            reminder.status = "cancelled"

        await session.commit()