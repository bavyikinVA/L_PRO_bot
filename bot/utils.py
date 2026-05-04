from datetime import datetime
from aiogram import Bot
from loguru import logger

from bot.keyboards.common import get_main_kb
from config import settings


def get_greeting_text(first_name: str, is_old_user: bool):
    if is_old_user:
        return f"""
С возвращением, <b>{first_name}</b>!

Рады видеть вас снова в PROmassage👋

Чем я могу вам помочь?
"""
    else:
        return f""" 
{first_name}, мы рады приветствовать вас в нашей цифровой системе записи на услуги. Здесь вы сможете:
    
✅ Записаться на процедуру к любому мастеру
🗓 Управлять своими записями
ℹ️ Получать информацию о наших услугах
    
<i>Ваше здоровье и фигура - наш главный приоритет!</i>
    
Чтобы начать, выберите нужный пункт меню ниже 👇
"""


def get_about_text():
    return """
💆‍♀️ <b>"PROmassage"</b>

Мы - современный салон методов аппаратной коррекции фигуры в Липецке, предоставляем комплекс услуг по уходу за собой и своей фигурой! 

<b>Наши услуги:</b>
• Аппаратный массаж тела 
• Обертывание
• Ультразвуковая чистка лица
• БАДы для похудения

<i>Мы заботимся о вашем здоровье и комфорте!</i>

Чтобы записаться на прием или узнать больше о наших услугах, воспользуйтесь меню бота.
"""


def get_booking_text(appointment_count):
    if appointment_count > 0:
        message_text = f"""
📅 <b>Ваши записи:</b>

У вас запланировано <b>{appointment_count}</b> {pluralize_appointments(appointment_count)}.

Чтобы просмотреть детали ваших записей, нажмите кнопку "Просмотреть записи" ниже.
"""
    else:
        message_text = """
📅 <b>Ваши записи</b>

В настоящее время у вас нет запланированных процедур.

Чтобы записаться к мастеру, воспользуйтесь кнопкой "Записаться".
"""
    return message_text


def pluralize_appointments(count: int) -> str:
    if count == 1:
        return "прием"
    elif 2 <= count <= 4:
        return "приема"
    else:
        return "приемов"


def format_appointment(specialist_name: str, service_name: str, booking_datetime: datetime) -> str:
    return f"""
🗓 <b>Запись на услугу</b>

📅 Дата: {booking_datetime.strftime('%d.%m.%Y')}
🕒 Время: {booking_datetime.strftime('%H:%M')}
🙌 Мастер: {specialist_name}
💆‍♀️ Услуга: {service_name}
"""


async def send_booking_notification(
        user_id: int | None,
        specialist_name: str,
        service_name: str,
        booking_datetime: datetime,
        client_full_name: str | None = None,
        client_phone: str | None = None,
):
    bot = Bot(token=settings.BOT_TOKEN)

    try:
        if user_id:
            await bot.send_message(
                chat_id=user_id,
                text=(
                    f"✅ Ваша запись успешно создана!\n\n"
                    f"👨‍💼 Специалист: {specialist_name}\n"
                    f"💆 Услуга: {service_name}\n"
                    f"📅 Дата и время: {booking_datetime.strftime('%d.%m.%Y %H:%M')}\n\n"
                    f"Пожалуйста, приходите за 5-10 минут до назначенного времени."
                ),
                parse_mode="HTML",
                reply_markup=get_main_kb()
            )
            logger.info(f"Уведомление отправлено пользователю ID {user_id}")
        else:
            logger.info("У клиента нет telegram_id, уведомление клиенту пропущено")

        admin_text = (
            f"🔔 <b>Новая запись клиента</b>\n\n"
            f"👤 Клиент: {client_full_name or 'не указан'}\n"
            f"📞 Телефон: {client_phone or 'не указан'}\n"
            f"👨‍💼 Мастер: {specialist_name}\n"
            f"💆 Услуга: {service_name}\n"
            f"📅 Дата и время: {booking_datetime.strftime('%d.%m.%Y %H:%M')}"
        )

        for admin_id in settings.ADMIN_IDS:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=admin_text,
                    parse_mode="HTML"
                )
                logger.info(f"Уведомление отправлено админу ID {admin_id}")
            except Exception as admin_error:
                logger.error(f"Ошибка при отправке админу ID {admin_id}: {admin_error}")

    except Exception as e:
        logger.error(f"Ошибка при отправке уведомлений о записи: {str(e)}")
    finally:
        await bot.session.close()