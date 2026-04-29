from config import settings
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import WebAppInfo


def get_main_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="📅 Мои записи", callback_data="my_booking")
    builder.button(text="🔖 Записаться", web_app=WebAppInfo(url=f"{settings.FRONT_SITE}"))
    builder.button(text="ℹ️ О нас", callback_data="about_us")
    builder.adjust(1)
    return builder.as_markup()


def get_back_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 Главное меню", callback_data="home")
    builder.button(text="🔖 Записаться", web_app=WebAppInfo(url=f"{settings.FRONT_SITE}"))
    builder.adjust(1)
    return builder.as_markup()


def generate_kb_profile(count_booking: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 Главное меню", callback_data="home")
    builder.button(text="🔖 Записаться", web_app=WebAppInfo(url=f"{settings.FRONT_SITE}"))

    if count_booking > 0:
        builder.button(
            text=f"✍️ Мои записи ({count_booking})",
            callback_data=f"my_booking_all"
        )

    builder.adjust(1)
    return builder.as_markup()
