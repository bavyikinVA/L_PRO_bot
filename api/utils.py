from datetime import date, datetime, timedelta, time
from calendar import monthrange
import locale
import pytz

# from app.bot.scheduler_task import schedule_appointment_notification

MOSCOW_TZ = pytz.timezone("Europe/Moscow")

"""
async def add_notification(user_tg_id, appointment, notification_time, reminder_label, notification_times):
    if notification_time > datetime.now(MOSCOW_TZ):
        await schedule_appointment_notification(
            user_tg_id=user_tg_id,
            appointment=appointment,
            notification_time=notification_time,
            reminder_label=reminder_label
        )
        notification_times.append(notification_time)
"""


locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')


def get_current_month_days():
    today = date.today()
    _, last_day = monthrange(today.year, today.month)

    days = []
    for day in range(1, last_day + 1):
        current_date = date(today.year, today.month, day)
        days.append({
            "date": current_date,
            "day_name": current_date.strftime("%A"),
            "weekday": current_date.weekday()
        })

    return days


def generate_time_slots(start_time: time, end_time: time, interval_minutes: int):
    slots = []
    current = datetime.combine(date.today(), start_time)
    end = datetime.combine(date.today(), end_time)

    while current < end:
        slots.append(current.time())
        current += timedelta(minutes=interval_minutes)

    return slots