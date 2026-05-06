# from datetime import datetime, timedelta
from aiogram.types import WebAppInfo
# from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import settings


def get_admin_main_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="📅 Мои записи", callback_data="my_booking")
    builder.button(text="🔖 Записаться", web_app=WebAppInfo(url=f"{settings.FRONT_SITE}"))
    builder.button(text="ℹ️ О нас", callback_data="about_us")
    builder.button(text="🔑 Админ панель", web_app=WebAppInfo(url=f"{settings.FRONT_SITE}/admin"))
    builder.adjust(1)
    return builder.as_markup()

#
# def get_admin_functions_kb():
#     builder = InlineKeyboardBuilder()
#     # builder.button(text="Получить список услуг", callback_data="get_all_services")
#     builder.button(text="Сгенерировать рабочее время", callback_data="set_schedule")
#     #builder.button(text="Добавить клиента", callback_data="add_new_user")
#     builder.button(text="Записать клиента", callback_data="create_new_booking")
#     builder.button(text="Расширенная админ-панель", callback_data="get_full_admin_kbs")
#     builder.button(text="Вернуться в главное меню", callback_data="home")
#     builder.adjust(1)
#     return builder.as_markup()
#
#
# def get_service_fields_kb():
#     builder = InlineKeyboardBuilder()
#     builder.button(text="Название", callback_data="update_service_name")
#     builder.button(text="Описание", callback_data="update_service_description")
#     builder.button(text="Цена", callback_data="update_service_price")
#     builder.adjust(1)
#     return builder.as_markup()
#
#
# def get_service_list_kb(services: list) -> InlineKeyboardMarkup:
#     keyboard = []
#
#     for service in services:
#         keyboard.append([
#             InlineKeyboardButton(
#                 text=f"{service.id} - {service.label}",
#                 callback_data=f"service_{service.id}"
#             )
#         ])
#
#     keyboard.append([
#         InlineKeyboardButton(
#             text="❌ Отмена",
#             callback_data="/cancel"
#         )
#     ])
#
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
#
# def get_admin_full_kbs():
#     builder = InlineKeyboardBuilder()
#     builder.button(text="Получить список услуг", callback_data="get_all_services") # есть
#     builder.button(text="Добавить услугу", callback_data="add_new_service") # есть
#     builder.button(text="Обновить данные услуги", callback_data="update_service") # есть
#     builder.button(text="Сгенерировать рабочее время", callback_data="set_schedule")
#     builder.button(text="Добавить клиента", callback_data="add_new_user") # есть
#     builder.button(text="Записать клиента", callback_data="create_new_booking")
#     builder.button(text="Добавить мастера", callback_data="add_new_master") # есть
#     builder.button(text="Изменить данные мастера", callback_data="update_specialist")
#     builder.button(text="Добавить услугу мастеру", callback_data="add_new_service_to_master")
#     # builder.button(text="Удалить услугу мастера", callback_data="delete_service_from_master")
#     # builder.button(text="Дать права админа", callback_data="make_user_to_admin")
#     builder.button(text="Вернуться в главное меню", callback_data="home")
#     builder.adjust(1)
#     return builder.as_markup()
#
#
# def get_masters_list_kb(masters: list) -> InlineKeyboardMarkup:
#     """Создает клавиатуру со списком мастеров"""
#     keyboard = []
#
#     for master in masters:
#         keyboard.append([
#             InlineKeyboardButton(
#                 text=f"{master.id} - {master.first_name} {master.last_name}",
#                 callback_data=f"master_{master.id}"
#             )
#         ])
#
#     keyboard.append([
#         InlineKeyboardButton(
#             text="❌ Отмена",
#             callback_data="cancel"
#         )
#     ])
#
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
#
# def get_specialist_fields_kb():
#     builder = InlineKeyboardBuilder()
#     builder.button(text="Имя", callback_data="update_specialist_first_name")
#     builder.button(text="Фамилия", callback_data="update_specialist_last_name")
#     builder.button(text="Стаж работы", callback_data="update_specialist_work_experience")
#     builder.button(text="Фото", callback_data="update_specialist_photo")
#     builder.adjust(1)
#     return builder.as_markup()
#

# def get_days_of_week(selected_days: set = None) -> InlineKeyboardMarkup:
#     """Создает клавиатуру с днями недели"""
#     if selected_days is None:
#         selected_days = set()
#
#     days = [
#         ("Понедельник", "mon"),
#         ("Вторник", "tue"),
#         ("Среда", "wed"),
#         ("Четверг", "thu"),
#         ("Пятница", "fri"),
#         ("Суббота", "sat"),
#         ("Воскресенье", "sun")
#     ]
#
#     keyboard = []
#
#     # кнопки дней недели
#     for day_name, day_code in days:
#         emoji = "✅" if day_code in selected_days else "⚪"
#         keyboard.append([
#             InlineKeyboardButton(
#                 text=f"{emoji} {day_name}",
#                 callback_data=f"day_{day_code}"
#             )
#         ])
#
#     # кнопки действий
#     keyboard.append([
#         InlineKeyboardButton(
#             text="✅ Выбрать все дни",
#             callback_data="select_all_days"
#         )
#     ])
#     keyboard.append([
#         InlineKeyboardButton(
#             text="❌ Отмена",
#             callback_data="cancel_schedule"
#         ),
#         InlineKeyboardButton(
#             text="➡️ Далее",
#             callback_data="days_selected"
#         )
#     ])
#
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)


# def get_time_interval_kb():
#     builder = ReplyKeyboardBuilder()
#     intervals = ["30", "60", "90", "120"]
#     for interval in intervals:
#         builder.add(KeyboardButton(text=f"{interval} минут"))
#
#     builder.add(KeyboardButton(text="❌ Отмена"))
#     builder.adjust(2)
#     return builder.as_markup(resize_keyboard=True)


# def get_confirmation_kb():
#     builder = ReplyKeyboardBuilder()
#     builder.add(KeyboardButton(text="✅ Подтвердить"))
#     builder.add(KeyboardButton(text="❌ Отмена"))
#     return builder.as_markup(resize_keyboard=True)


# def get_month_selection_kb() -> InlineKeyboardMarkup:
#     current_date = datetime.now()
#     # текущий месяц
#     buttons = [[
#         InlineKeyboardButton(
#             text=f"{current_date.strftime('%B %Y')} (текущий)",
#             callback_data=f"month_{current_date.month}_{current_date.year}"
#         )
#     ]]
#     # следующие 3 месяца
#     for i in range(1, 4):
#         next_date = current_date + timedelta(days=30 * i)
#         buttons.append([
#             InlineKeyboardButton(
#                 text=next_date.strftime('%B %Y'),
#                 callback_data=f"month_{next_date.month}_{next_date.year}"
#             )
#         ])
#
#     buttons.append([
#         InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_schedule")
#     ])
#
#     return InlineKeyboardMarkup(inline_keyboard=buttons)