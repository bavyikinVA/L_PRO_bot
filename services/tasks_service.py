from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests
from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from celery_app import app
from config import settings
from database.models import Booking, BookingReminder
from services.sync_database import SyncSessionLocal

MSK = ZoneInfo("Europe/Moscow")

# допустимая задержка выполнения Celery-задачи.
MAX_REMINDER_DELAY_SECONDS = 120


def get_hour_word(hours_before: int) -> str:
    if hours_before == 1:
        return "час"
    if hours_before in (6, 12):
        return "часов"
    if hours_before == 24:
        return "часа"
    return "часов"


def send_reminder_notification(
    user_id: int,
    specialist_name: str,
    service_name: str,
    booking_datetime: datetime,
    hours_before: int,
) -> bool:
    """Синхронная отправка напоминания через Telegram Bot API."""

    logger.info(f"Отправка напоминания пользователю ID {user_id} за {hours_before} ч.")

    try:
        booking_dt_msk = (
            booking_datetime.astimezone(MSK)
            if booking_datetime.tzinfo
            else booking_datetime.replace(tzinfo=MSK)
        )

        hour_word = get_hour_word(hours_before)

        message = (
            f"⏰ <b>Напоминание о записи!</b>\n\n"
            f"⏳ Через <b>{hours_before} {hour_word}</b> у вас запись!\n\n"
            f"👨‍💼 Специалист: {specialist_name}\n"
            f"💆 Услуга: {service_name}\n"
            f"📅 Дата и время: <b>{booking_dt_msk.strftime('%d.%m.%Y %H:%M')}</b>\n\n"
            f"🕐 Пожалуйста, приходите за 5-10 минут до назначенного времени."
        )

        url = f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": user_id,
            "text": message,
            "parse_mode": "HTML",
        }

        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()

        logger.info(
            f"Напоминание успешно отправлено пользователю ID {user_id} "
            f"за {hours_before} ч."
        )
        return True

    except Exception as e:
        logger.error(
            f"Ошибка при отправке напоминания пользователю ID {user_id}: {str(e)}"
        )
        return False


@app.task(bind=True, max_retries=3)
def send_reminder(self, reminder_id: int):
    """
    Celery-задача отправки напоминания.

    Важно:
    - reminder_id — это ID строки из booking_reminders.
    - БД является источником истины.
    - Celery/Redis только доставляют задачу.
    """

    task_id = self.request.id
    logger.info(f"Запуск напоминания reminder_id={reminder_id}, task_id={task_id}")

    with SyncSessionLocal() as session:
        try:
            reminder = session.execute(
                select(BookingReminder).where(reminder_id == BookingReminder.id)
            ).scalar_one_or_none()

            if not reminder:
                logger.warning(f"Напоминание ID={reminder_id} не найдено")
                return {"status": "skipped", "reason": "reminder_not_found"}

            if reminder.status in ["sent", "cancelled", "skipped", "processing"]:
                logger.info(
                    f"Напоминание ID={reminder_id} уже обработано: {reminder.status}"
                )
                return {"status": "skipped", "reason": f"already_{reminder.status}"}

            if reminder.status != "scheduled":
                logger.info(
                    f"Напоминание ID={reminder_id} имеет неподходящий статус: "
                    f"{reminder.status}"
                )
                return {"status": "skipped", "reason": f"status_{reminder.status}"}

            now_msk = datetime.now(MSK)

            remind_at_msk = (
                reminder.remind_at.astimezone(MSK)
                if reminder.remind_at.tzinfo
                else reminder.remind_at.replace(tzinfo=MSK)
            )

            if now_msk > remind_at_msk + timedelta(seconds=MAX_REMINDER_DELAY_SECONDS):
                reminder.status = "skipped"
                reminder.error_message = "reminder_time_missed"
                session.commit()

                logger.warning(
                    f"Напоминание ID={reminder_id} пропущено: "
                    f"remind_at={remind_at_msk}, now={now_msk}, "
                    f"hours_before={reminder.hours_before}"
                )

                return {
                    "status": "skipped",
                    "reason": "reminder_time_missed",
                    "reminder_id": reminder.id,
                }

            reminder.status = "processing"
            session.commit()

            booking = session.execute(
                select(Booking)
                .options(
                    joinedload(Booking.specialist),
                    joinedload(Booking.service),
                    joinedload(Booking.user),
                )
                .where(Booking.id == reminder.booking_id)
            ).scalars().first()

            if not booking:
                reminder.status = "skipped"
                reminder.error_message = "booking_not_found"
                session.commit()
                return {"status": "skipped", "reason": "booking_not_found"}

            if booking.status != "confirmed" or booking.is_cancelled:
                reminder.status = "cancelled"
                reminder.error_message = "booking_cancelled"
                session.commit()
                return {"status": "skipped", "reason": "booking_cancelled"}

            booking_dt_msk = (
                booking.booking_datetime.astimezone(MSK)
                if booking.booking_datetime.tzinfo
                else booking.booking_datetime.replace(tzinfo=MSK)
            )

            if booking_dt_msk <= now_msk:
                reminder.status = "skipped"
                reminder.error_message = "booking_already_started"
                session.commit()
                return {"status": "skipped", "reason": "booking_already_started"}

            if not booking.user or not booking.specialist or not booking.service:
                reminder.status = "failed"
                reminder.error_message = "missing_booking_relations"
                session.commit()
                return {"status": "failed", "reason": "missing_booking_relations"}

            success = send_reminder_notification(
                user_id=booking.user.telegram_id,
                specialist_name=(
                    f"{booking.specialist.first_name} {booking.specialist.last_name}"
                ),
                service_name=booking.service.label,
                booking_datetime=booking.booking_datetime,
                hours_before=reminder.hours_before,
            )

            if success:
                reminder.status = "sent"
                reminder.sent_at = datetime.now(MSK)
                reminder.error_message = None
                session.commit()

                logger.info(f"Напоминание ID={reminder_id} успешно отправлено")
                return {"status": "sent", "reminder_id": reminder.id}

            reminder.status = "failed"
            reminder.error_message = "notification_failed"
            session.commit()

            logger.warning(f"Напоминание ID={reminder_id} не отправлено, будет retry")
            raise self.retry(countdown=300)

        except Exception as e:
            session.rollback()
            logger.error(
                f"Ошибка в задаче reminder_id={reminder_id}, "
                f"task_id={task_id}: {str(e)}"
            )

            reminder = session.execute(
                select(BookingReminder).where(reminder_id == BookingReminder.id)
            ).scalar_one_or_none()

            if reminder:
                reminder.status = "failed"
                reminder.error_message = str(e)[:255]
                session.commit()

            raise