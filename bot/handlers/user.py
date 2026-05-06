from zoneinfo import ZoneInfo
from aiogram import Router, F
from aiogram import flags
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from fastapi import HTTPException
from loguru import logger

from api.dao import UserDAO
from api.schemas import UserModel, UserUpdateModel
from bot.keyboards.admin import get_admin_main_kb
from bot.keyboards.common import get_back_kb, get_main_kb, generate_kb_profile
from bot.states.user import UserStates
from bot.utils import get_greeting_text, get_about_text, get_booking_text, format_appointment
from config import settings
from database.database import async_session_maker
from services.booking_service import BookingService
from services.service_service import ServiceService
from services.specialist_service import SpecialistServiceClass
from services.user_service import UserService


router = Router()

@router.message(CommandStart())
@flags.chat_action("typing")
async def cmd_start(message: Message, state: FSMContext):
    async with async_session_maker() as session:
        try:
            logger.info(f"Получена команда /start от {message.from_user.id}")

            user_info = {
                "telegram_id": message.from_user.id,
                "username": message.from_user.username,
                "first_name": message.from_user.first_name,
                "last_name": message.from_user.last_name
            }

            user_in_db = await UserService.get_user_by_telegram_id(session=session,
                                                                   telegram_id=user_info["telegram_id"])
            if user_in_db is not None:
                greeting_message = get_greeting_text(user_info.get("first_name"), True)
                if user_info["telegram_id"] in settings.ADMIN_IDS:
                    await message.answer(greeting_message, reply_markup=get_admin_main_kb())
                else:
                    await message.answer(greeting_message, reply_markup=get_main_kb())
            else:
                await message.answer(
                    "Добро пожаловать в телеграм бот <b>PROMassage!</b>👋\n"
                    "Давайте зарегистрируем вас в системе. \n\n"
                    "<b>Мы не передаем ваши контактные данные третьим лицам. "
                    "Они нужны для того, чтобы наши мастера смогли связаться с вами!</b> 😊",
                    parse_mode="HTML")
                await message.answer("Пожалуйста, введите ваше полное имя (пример: Фамилия Имя Отчество):")
                await state.set_state(UserStates.waiting_for_user_full_name)
                await state.update_data(user_info=user_info)

        except Exception as e:
            logger.error(f"Ошибка в обработчике /start: {e}")
            await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")


@router.message(UserStates.waiting_for_user_full_name)
async def process_full_name(message: Message, state: FSMContext):
    full_name = message.text.strip()
    parts = full_name.split()
    if len(parts) < 2:
        await message.answer("Пожалуйста, введите полное имя в формате 'Фамилия Имя Отчество'")
        return

    last_name = parts[0]
    first_name = parts[1]
    patronymic = parts[2] if len(parts) > 2 else None

    await state.update_data({
        "last_name": last_name,
        "first_name": first_name,
        "patronymic": patronymic
    })
    await message.answer(
        "Теперь введите ваш номер телефона в формате 89XXXXXXXXX:"
    )
    await state.set_state(UserStates.waiting_for_user_phone_number)


@router.message(UserStates.waiting_for_user_phone_number)
async def process_phone(message: Message, state: FSMContext):
    async with async_session_maker() as session:
        phone = message.text.strip()
        if not phone.isdigit() or len(phone) != 11 or not phone.startswith('89'):
            await message.answer("Пожалуйста, введите корректный номер телефона (11 цифр, начинается с 89)")
            return

        data = await state.get_data()
        logger.debug(f"State data: {data}")
        user_info = data.get("user_info", {})
        logger.debug(f"User info: {user_info}")

        if not user_info.get("telegram_id"):
            logger.error(f"telegram_id is missing for user {message.from_user.id}")
            await message.answer("Ошибка: Telegram ID отсутствует. Попробуйте начать заново с /start.")
            await state.clear()
            return

        # ищем в бд пользователя на случай если админ самостоятельно добавлял данные
        existing_user = await UserDAO.find_existing_user(
            session=session,
            first_name=data["first_name"],
            last_name=data.get("last_name"),
            phone_number=phone
        )

        try:
            if existing_user:
                if not hasattr(existing_user, 'id') or existing_user.id is None:
                    logger.error(f"existing_user has no valid id: {existing_user.model_dump()}")
                    raise ValueError("Найденный пользователь не имеет действительного ID")
                update_data = UserUpdateModel(
                    telegram_id=user_info["telegram_id"],
                    username=user_info.get("username"),
                    is_admin=(user_info["telegram_id"] in settings.ADMIN_IDS)
                )
                logger.info(f"Updating existing user ID {existing_user.id} with: {update_data.model_dump()}")
                updated_user = await UserService.update_user(
                    session=session,
                    user_id=existing_user.id,
                    update_data=update_data
                )
                await message.answer(
                    "Ваш Telegram аккаунт успешно привязан к существующей записи!\n"
                    f"Добро пожаловать, {data['first_name']}!",
                    reply_markup=get_admin_main_kb() if updated_user.is_admin else get_main_kb()
                )
            else:
                user_data = UserModel(
                    telegram_id=user_info["telegram_id"],
                    username=user_info.get("username"),
                    first_name=data["first_name"],
                    last_name=data.get("last_name"),
                    patronymic=data.get("patronymic"),
                    phone_number=phone,
                    is_admin=user_info["telegram_id"] in settings.ADMIN_IDS
                )
                logger.info(f"Creating new user: {user_data.model_dump()}")
                await UserService.create_user(session=session, user_data=user_data)
                await message.answer(text="Регистрация завершена!")

                greeting_message = get_greeting_text(data.get("first_name"), False)
                if user_info["telegram_id"] in settings.ADMIN_IDS:
                    await message.answer(greeting_message, reply_markup=get_admin_main_kb())
                else:
                    await message.answer(greeting_message, reply_markup=get_main_kb())

        except HTTPException as e:
            logger.error(f"HTTPException during user registration: {str(e)}")
            await message.answer(f"❌ Ошибка: {e.detail}")
        except ValueError as e:
            logger.error(f"ValueError during user registration: {str(e)}")
            await message.answer(f"❌ Ошибка: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during user registration: {str(e)}")
            await message.answer("❌ Произошла ошибка при регистрации. Пожалуйста, попробуйте позже.")
        finally:
            try:
                await state.clear()
                logger.info(f"State cleared for user {message.from_user.id}")
            except Exception as e:
                logger.error(f"Error clearing state for user {message.from_user.id}: {str(e)}")

@router.callback_query(F.data == "home")
async def handler_back_home(callback: CallbackQuery):
    await callback.answer("Главное меню")
    await callback.message.answer(
        "Вы на главной странице!\nДля выполнения операций выберите кнопку ниже",
            reply_markup=(get_admin_main_kb() if callback.from_user.id in settings.ADMIN_IDS else get_main_kb())
        )

@router.callback_query(F.data == "my_booking")
async def handler_my_appointments(callback: CallbackQuery):
    await callback.answer("Ваши ближайшие записи:")
    async with async_session_maker() as session:
        db_user_id = await UserService.get_user_by_telegram_id(
            session=session,
            telegram_id=callback.from_user.id)
        appointment_count = await BookingService.count_user_booking(
            session=session,
            user_id=db_user_id.id)
        message_text = get_booking_text(appointment_count)
        keyboard = generate_kb_profile(appointment_count)
        await callback.message.answer(message_text, reply_markup=keyboard)

@router.callback_query(F.data.startswith("my_booking_all"))
async def handler_my_appointments_all(callback: CallbackQuery):
    await callback.answer("Ваши ближайшие записи (подробно)")
    async with async_session_maker() as session:
        try:
            user = await UserService.get_user_by_telegram_id(session=session, telegram_id=callback.from_user.id)
            logger.debug(
                f"Telegram ID {callback.from_user.id} -> User ID {user.id if user else 'не найден'}")

            appointments = await BookingService.get_user_bookings(
                session=session,
                telegram_id=callback.from_user.id
            )

            if not appointments:
                await callback.message.answer("У вас нет активных записей.", reply_markup=get_main_kb())
                logger.info(f"Нет бронирований для Telegram ID {callback.from_user.id}")
                return

            await callback.message.answer("📅 Ваши записи:")

            msk_tz = ZoneInfo("Europe/Moscow")

            for appointment in appointments:
                service = await ServiceService.get_service(session, appointment.service_id)
                specialist = await SpecialistServiceClass.get_specialist(session, appointment.specialist_id)

                booking_datetime_msk = appointment.booking_datetime.astimezone(msk_tz)

                message_text = format_appointment(
                    specialist_name=f"{specialist.first_name} {specialist.last_name}",
                    booking_datetime=booking_datetime_msk,
                    service_name=service.label
                )
                await callback.message.answer(text=message_text)


            await callback.message.answer("Это все ваши текущие записи.", reply_markup=get_main_kb())
            logger.info(f"Выведено {len(appointments)} бронирований для Telegram ID {callback.from_user.id}")

        except HTTPException as e:
            await callback.message.answer(f"❌ Ошибка: {e.detail}", reply_markup=get_main_kb())
            logger.error(f"HTTPException при получении бронирований: {e.detail}, Telegram ID={callback.from_user.id}")
        except Exception as e:
            await callback.message.answer("❌ Произошла ошибка при получении записей.", reply_markup=get_main_kb())
            logger.error(f"Ошибка при получении бронирований: {str(e)}, Telegram ID={callback.from_user.id}")


@router.callback_query(F.data == "about_us")
async def handler_about_us(callback: CallbackQuery):
    await callback.answer("О нас")
    about_us_text = get_about_text()
    await callback.message.answer(about_us_text, reply_markup=get_back_kb())
