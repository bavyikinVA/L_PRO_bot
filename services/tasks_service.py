import requests
from loguru import logger
from datetime import datetime
from zoneinfo import ZoneInfo

from config import settings
from celery_app import app
from services.sync_database import get_booking_with_relations

MSK = ZoneInfo("Europe/Moscow")


def send_reminder_notification(
        user_id: int,
        specialist_name: str,
        service_name: str,
        booking_datetime: datetime,
        hours_before: int
):
    """Синхронная функция для отправки напоминания через Telegram API."""
    logger.info(f"Отправка напоминания пользователю ID {user_id} за {hours_before} ч.")
    try:
        booking_dt_msk = booking_datetime.astimezone(MSK) if booking_datetime.tzinfo else booking_datetime.replace(
            tzinfo=MSK)
        change = ""
        if hours_before == 1:
            change = 'час'
        elif hours_before == 6 or hours_before == 12:
            change = 'часов'
        elif hours_before == 24:
            change = 'часа'
        message = (
            f"⏰ <b>Напоминание о записи!</b>\n\n"
            f"⏳ Через <b>{hours_before} {change}</b> у вас запись!\n\n"
            f"👨‍💼 Специалист: {specialist_name}\n"
            f"💆 Услуга: {service_name}\n"
            f"📅 Дата и время: <b>{booking_dt_msk.strftime('%d.%m.%Y %H:%M')}</b>\n\n"
            f"🕐 Пожалуйста, приходите за 5-10 минут до назначенного времени."
        )

        url = f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": user_id,
            "text": message,
            "parse_mode": "HTML"
        }
        logger.debug(f"Отправка запроса к Telegram API: {url}")
        response = requests.post(url, json=payload)
        response.raise_for_status()
        logger.info(f"Напоминание успешно отправлено пользователю ID {user_id} за {hours_before} ч.")
        return True
    except Exception as e:
        logger.error(f"Ошибка при отправке напоминания пользователю ID {user_id}: {str(e)}")
        return False


@app.task(bind=True)
def send_reminder(self, booking_id: int, hours_before: int):
    """Синхронная Celery задача для отправки напоминания."""
    task_id = self.request.id
    logger.info(f"Начало выполнения задачи напоминания для брони {booking_id}, task_id={task_id}")

    try:
        booking = get_booking_with_relations(booking_id)

        if not booking:
            logger.warning(f"Бронь ID {booking_id} не найдена для напоминания {task_id}")
            return {"status": "skipped", "reason": "booking_not_found"}

        logger.debug(
            f"Найдена бронь: ID={booking_id}, status={booking.status}, is_cancelled={booking.is_cancelled}")

        if booking.status != "confirmed" or booking.is_cancelled:
            logger.info(f"Бронь ID {booking_id} отменена/не подтверждена, напоминание {task_id} пропущено")
            return {"status": "skipped", "reason": "booking_cancelled"}

        current_msk = datetime.now(MSK)
        booking_dt_msk = booking.booking_datetime.astimezone(MSK)
        time_until_booking = booking_dt_msk - current_msk
        actual_hours_left = time_until_booking.total_seconds() / 3600
        logger.debug(f"Время до брони: {actual_hours_left:.1f}ч, ожидалось: {hours_before}ч")

        if actual_hours_left < (hours_before - 0.25):
            logger.warning(
                f"Напоминание устарело: ожидалось {hours_before}ч, осталось {actual_hours_left:.1f}ч. "
                f"Task {task_id} отменен"
            )
            return {"status": "skipped", "reason": "time_expired"}

        specialist = booking.specialist
        service = booking.service
        user = booking.user

        if not specialist or not service or not user:
            logger.error(f"Не удалось получить данные для брони {booking_id}")
            return {"status": "failed", "reason": "missing_data"}

        logger.debug(f"Специалист: {specialist.first_name} {specialist.last_name}, Услуга: {service.label}")

        # Отправляем напоминание
        success = send_reminder_notification(
            user_id=user.telegram_id,
            specialist_name=f"{specialist.first_name} {specialist.last_name}",
            service_name=service.label,
            booking_datetime=booking.booking_datetime,
            hours_before=hours_before
        )

        if success:
            logger.info(f"Напоминание за {hours_before}ч успешно отправлено для брони {booking_id}")
            return {"status": "sent", "booking_id": booking_id, "task_id": task_id}
        else:
            logger.error(f"Не удалось отправить напоминание для брони {booking_id}")
            return {"status": "failed", "reason": "notification_failed"}

    except Exception as e:
        logger.error(f"Ошибка в задаче напоминания {task_id}: {str(e)}")
        if self.request.retries < 3:
            logger.info(f"Повторная попытка для задачи {task_id} через 5 минут")
            raise self.retry(countdown=60 * 5)
        else:
            logger.error(f"Исчерпаны попытки retry для задачи {task_id}")
            return {"status": "failed", "error": str(e)}