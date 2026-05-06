# import os
# from datetime import datetime
#
# from aiogram import Router, F
# from aiogram.enums import ParseMode
# from aiogram.filters import Command
# from aiogram.fsm.context import FSMContext
# from aiogram.types import Message, CallbackQuery
# from fastapi import HTTPException
# from loguru import logger
#
# from api.dao import SpecialistDAO, ScheduleDAO
# from api.schemas import ServiceCreate, UserModel, SpecialistCreate, ServiceUpdate, \
#     SpecialistServiceCreate, SpecialistUpdate
# from bot.keyboards.admin import get_admin_functions_kb, get_service_fields_kb, get_admin_full_kbs, \
#     get_masters_list_kb, get_days_of_week, get_service_list_kb, \
#     get_month_selection_kb, get_specialist_fields_kb
# from bot.states.admin import AdminStates, CreateNewUserStates, CreateNewMasterStates, AddToMasterServiceStates, \
#     SetMasterScheduleStates, UpdateMasterStates
# from config import settings
# from database.database import async_session_maker
# from services.service_service import ServiceService
# from services.specialist_service import SpecialistServiceClass
# from services.user_service import UserService
#
# router = Router()
#
# async def get_session():
#     async with async_session_maker() as session:
#         yield session
#
#
# @router.callback_query(F.data == "admin_panel")
# async def handler_main_admin_panel(callback: CallbackQuery):
#     await callback.answer("Переход в админ панель")
#     await callback.message.answer(
#         "Добро пожаловать в панель администратора!\n"
#         "Приступим к работе?\nВыберите необходимую функцию ниже:",
#         reply_markup=get_admin_functions_kb()
#     )
#
#
# @router.callback_query(F.data == "get_full_admin_kbs")
# async def handler_full_admin_panel(callback: CallbackQuery):
#     await callback.answer("Переходим в режим расширенной панели инструментов")
#     await callback.message.answer(
#         "Выберите команду из меню расширенных настроек:\n", reply_markup=get_admin_full_kbs()
#     )
#
#
# @router.callback_query(F.data == "add_new_service")
# async def handler_add_new_service(callback: CallbackQuery, state: FSMContext):
#     logger.info(f"Admin {callback.from_user.id} initiated adding new service")
#     await callback.message.answer(
#         "Для добавления новой услуги или продукта следуйте следующим указаниям:\n"
#         "Введите <b>название</b> услуги/продукта.", parse_mode=ParseMode.HTML
#     )
#     await state.set_state(AdminStates.waiting_for_service_name)
#
# @router.message(AdminStates.waiting_for_service_name)
# async def process_service_name(message: Message, state: FSMContext):
#     service_name = message.text.strip()
#     logger.info(f"Admin {message.from_user.id} entered service name: {service_name}")
#     await state.update_data(service_name=service_name)
#     await message.answer(
#         f"Вы ввели название услуги: {service_name}\n"
#         "Теперь введите <b>описание</b> услуги:", parse_mode=ParseMode.HTML
#     )
#     await state.set_state(AdminStates.waiting_for_service_description)
#
#
# @router.message(AdminStates.waiting_for_service_description)
# async def process_service_description(message: Message, state: FSMContext):
#     service_description = message.text.strip()
#     logger.info(f"Admin {message.from_user.id} entered service description: {service_description}")
#     await state.update_data(service_description=service_description)
#     await message.answer(
#         "Теперь введите <b>стоимость</b> услуги в рублях (только число):",
#         parse_mode=ParseMode.HTML
#     )
#     await state.set_state(AdminStates.waiting_for_service_price)
#
# @router.message(AdminStates.waiting_for_service_price)
# async def process_service_price(message: Message, state: FSMContext):
#     logger.info(f"Admin {message.from_user.id} entered service price: {message.text}")
#     async with async_session_maker() as session:
#         try:
#             price = int(message.text.strip())
#             if price <= 0:
#                 logger.warning(f"Invalid price entered by {message.from_user.id}: {price}")
#                 await message.answer("Пожалуйста, введите положительную сумму (только число).")
#                 return
#
#             data = await state.get_data()
#             logger.debug(f"Collected service data: {data}")
#             service_data = ServiceCreate(
#                 label=data['service_name'],
#                 description=data['service_description'],
#                 price=price,
#                 duration_minutes=120
#             )
#             logger.info(f"Creating service with data: {service_data.model_dump()}")
#             result = await ServiceService.create_service(
#                 session=session,
#                 service_data=service_data
#             )
#
#             await message.answer(
#                 f"✅ Услуга успешно создана!\n\n"
#                 f"Название: {result.label}\n"
#                 f"Описание: {result.description}\n"
#                 f"Стоимость: {result.price} руб.\n\n"
#                 f"Для привязки к мастеру выберите соответствующую команду в админ-панели",
#                 reply_markup=get_admin_functions_kb()
#             )
#             logger.info(f"Admin {message.from_user.id} created service: {result.label}")
#         except ValueError as e:
#             logger.warning(f"Invalid price format by {message.from_user.id}: {message.text}, error: {str(e)}")
#             await message.answer("Пожалуйста, введите корректную сумму (только число).")
#         except HTTPException as e:
#             logger.error(f"HTTPException while creating service by {message.from_user.id}: {str(e)}")
#             await message.answer(f"❌ Ошибка: {e.detail}")
#         except Exception as e:
#             logger.error(f"Unexpected error while creating service by {message.from_user.id}: {str(e)}")
#             await message.answer("❌ Произошла ошибка при создании услуги. Подробности в логах.")
#         finally:
#             try:
#                 await state.clear()
#                 logger.info(f"State cleared for user {message.from_user.id}")
#             except Exception as e:
#                 logger.error(f"Error clearing state for user {message.from_user.id}: {str(e)}")
#
#
# @router.message(Command("cancel"))
# @router.message(F.text.lower() == "отмена")
# async def cancel_handler(message: Message, state: FSMContext):
#     await state.clear()
#     await message.answer("Операция отменена", reply_markup=get_admin_functions_kb())
#
#
# @router.callback_query(F.data == "get_all_services")
# async def handler_get_all_services(callback: CallbackQuery):
#     async with async_session_maker() as session:
#         try:
#             await callback.answer()
#             services = await ServiceService.get_services(session=session)
#             if not services:
#                 await callback.message.answer("ℹ️ Список услуг пуст")
#                 return
#
#             services_list = "📋 Актуальный список услуг:\n\n"
#             for service in services:
#                 services_list += (
#                     f"🔹 {service.id}) {service.label or 'Без названия'}\n"
#                     f"📝 {service.description or 'Описание отсутствует'}\n"
#                     f"💵 Цена: {service.price} руб.\n\n"
#                 )
#
#             # разбиваем сообщение если слишком длинное
#             if len(services_list) > 4000:
#                 parts = [services_list[i:i + 4000] for i in range(0, len(services_list), 4000)]
#                 for part in parts:
#                     await callback.message.answer(part)
#             else:
#                 await callback.message.answer(services_list)
#
#             await callback.message.answer(text="Продолжим работу?\n", reply_markup=get_admin_functions_kb())
#
#         except Exception as e:
#             logger.error(f"Error getting services: {e}")
#             await callback.message.answer("⚠️ Произошла ошибка при получении списка услуг")
#
#
# @router.callback_query(F.data == "update_service")
# async def handler_update_service(callback: CallbackQuery, state: FSMContext):
#     async with async_session_maker() as session:
#         await callback.answer()
#         services = await ServiceService.get_services(session=session)
#         if not services:
#             await callback.message.answer("ℹ️ Список услуг пуст")
#             return
#
#         await callback.message.answer(
#             "Выберите услугу для обновления",
#             reply_markup=get_service_list_kb(services)
#         )
#         await state.set_state(AdminStates.waiting_for_service_id_to_update)
#
#
# @router.callback_query(AdminStates.waiting_for_service_id_to_update, F.data.startswith("service_"))
# async def process_service_id_to_update(callback: CallbackQuery, state: FSMContext):
#     async with async_session_maker() as session:
#         try:
#             service_id = int(callback.data.replace("service_", ""))
#             service = await ServiceService.get_service(session=session, service_id=service_id)
#             await state.update_data(service_id=service_id)
#             await callback.message.answer(
#                 f"Услуга найдена:\n\n"
#                 f"ID: {service.id}\n"
#                 f"Название: {service.label}\n"
#                 f"Описание: {service.description}\n"
#                 f"Цена: {service.price} руб.\n\n"
#                 "Выберите поле для изменения:",
#                 reply_markup=get_service_fields_kb()
#             )
#             await state.set_state(AdminStates.waiting_for_service_field_to_update)
#         except ValueError:
#             await callback.message.answer("⚠️ Пожалуйста, введите корректный ID (число)")
#         except HTTPException as e:
#             await callback.message.answer(f"❌ Ошибка: {e.detail}")
#             await state.clear()
#
#
# @router.callback_query(AdminStates.waiting_for_service_field_to_update)
# async def process_field_to_update(callback: CallbackQuery, state: FSMContext):
#     field_action = callback.data
#     field_map = {
#         "update_service_name": "новое название",
#         "update_service_description": "новое описание",
#         "update_service_price": "новую цену"
#     }
#
#     await state.update_data(field_to_update=field_action)
#     await callback.message.answer(
#         f"Введите {field_map.get(field_action, 'значение')}:"
#     )
#     await callback.answer()
#     await state.set_state(AdminStates.waiting_for_service_new_value)
#
#
# @router.message(AdminStates.waiting_for_service_new_value)
# async def process_new_value(message: Message, state: FSMContext):
#     async with async_session_maker() as session:
#         try:
#             data = await state.get_data()
#             service_id = data['service_id']
#             field = data['field_to_update']
#             new_value = message.text
#             update_data = ServiceUpdate()
#             if field == "update_service_name":
#                 update_data.label = new_value
#             elif field == "update_service_description":
#                 update_data.description = new_value
#             elif field == "update_service_price":
#                 try:
#                     update_data.price = int(new_value)
#                 except ValueError:
#                     await message.answer("Пожалуйста, введите корректную цену (число)")
#                     return
#             updated_service = await ServiceService.update_service(
#                 session=session,
#                 service_id=service_id,
#                 update_data=update_data
#             )
#             await message.answer(
#                 f"✅ Услуга успешно обновлена!\n\n"
#                 f"ID: {updated_service.id}\n"
#                 f"Название: {updated_service.label}\n"
#                 f"Описание: {updated_service.description}\n"
#                 f"Цена: {updated_service.price} руб.",
#                 reply_markup=get_admin_functions_kb()
#             )
#             logger.info(f"Service {service_id} updated. Changes: {update_data.model_dump()}")
#         except HTTPException as e:
#             await message.answer(f"❌ Ошибка: {e.detail}")
#         except Exception as e:
#             logger.error(f"Ошибка при обновлении услуги: {str(e)}")
#             await message.answer("❌ Произошла ошибка при обновлении услуги")
#         finally:
#             await state.clear()
#
#
# @router.callback_query(F.data == "add_new_user")
# async def handler_add_new_user(callback: CallbackQuery, state: FSMContext):
#     await callback.answer()
#     await callback.message.answer(text="Для добавления нового клиента вводите данные согласно инструкциям бота.\n")
#     await callback.message.answer(text="Введите ФИО клиента (пример: <b>Иванов Иван или Иванов Иван Иванович</b>):",
#                                   parse_mode=ParseMode.HTML)
#     await state.set_state(CreateNewUserStates.waiting_for_user_full_name)
#
#
# @router.message(CreateNewUserStates.waiting_for_user_full_name)
# async def process_full_user_name(message: Message, state: FSMContext):
#     full_name = message.text.strip()
#     parts = full_name.split()
#
#     last_name = parts[0]
#     first_name = parts[1]
#     patronymic = parts[2] if len(parts) > 2 else None
#
#     await state.update_data({
#         "last_name": last_name,
#         "first_name": first_name,
#         "patronymic": patronymic
#     })
#     await message.answer(
#         "Введите номер телефона в формате 89XXXXXXXXX:"
#     )
#     await state.set_state(CreateNewUserStates.waiting_for_user_phone_number)
#
#
# @router.message(CreateNewUserStates.waiting_for_user_phone_number)
# async def process_client_phone(message: Message, state: FSMContext):
#     async with async_session_maker() as session:
#         phone = message.text.strip()
#         if not phone.isdigit() or len(phone) != 11 or not phone.startswith('89'):
#             await message.answer("Пожалуйста, введите корректный номер телефона (11 цифр, начинается с 89)")
#             return
#
#         data = await state.get_data()
#         logger.debug(f"State data for client creation: {data}")
#         try:
#             user_data = UserModel(
#                 telegram_id=None,
#                 username=None,
#                 first_name=data["first_name"],
#                 last_name=data.get("last_name"),
#                 patronymic=data.get("patronymic"),
#                 phone_number=phone,
#                 is_admin=False
#             )
#             logger.info(f"Creating client: {user_data.model_dump()}")
#             user = await UserService.create_user(session=session, user_data=user_data)
#             await message.answer(f"Клиент {user.first_name} успешно зарегистрирован!",
#                                  reply_markup=get_admin_functions_kb())
#         except HTTPException as e:
#             logger.error(f"HTTPException while creating client: {str(e)}")
#             await message.answer(f"❌ Ошибка: {e.detail}")
#         except Exception as e:
#             logger.error(f"Error creating client: {str(e)}")
#             await message.answer("❌ Ошибка при создании клиента. Попробуйте снова.")
#         finally:
#             try:
#                 await state.clear()
#                 logger.info(f"State cleared for admin {message.from_user.id}")
#             except Exception as e:
#                 logger.error(f"Error clearing state for admin {message.from_user.id}: {str(e)}")
#
#
# @router.callback_query(F.data == "add_new_master")
# async def handler_add_new_master(callback: CallbackQuery, state: FSMContext):
#     logger.info(f"Вызван handler_add_new_master для user_id={callback.from_user.id}")
#     await callback.answer()
#     await callback.message.answer("Для добавления нового мастера укажите следующие данные:")
#     await callback.message.answer("Введите <b>фамилию и имя</b> мастера через пробел ( <b>пример: Иванов Иван</b> )")
#     await state.set_state(CreateNewMasterStates.waiting_for_master_full_name)
#     logger.info(f"Установлено состояние waiting_for_master_full_name для user_id={callback.from_user.id}")
#
# @router.message(CreateNewMasterStates.waiting_for_master_full_name)
# async def process_master_full_name(message: Message, state: FSMContext):
#     logger.info(f"Получен ввод для process_master_full_name: {message.text}, user_id={message.from_user.id}")
#     try:
#         full_name = message.text.strip()
#         name_parts = full_name.split()
#         if len(name_parts) < 2:
#             await message.answer("❌ Пожалуйста, введите фамилию и имя через пробел (например, Иванов Иван)")
#             return
#         last_name = name_parts[0]
#         first_name = name_parts[1]
#
#         await state.update_data({
#             "last_name": last_name,
#             "first_name": first_name,
#         })
#         await message.answer(
#             "Введите стаж работы мастера (число и год/года/лет, например, <i>5 лет</i> )"
#         )
#         await state.set_state(CreateNewMasterStates.waiting_for_master_work_experience)
#         logger.info(f"Сохранены данные: last_name={last_name}, first_name={first_name}, user_id={message.from_user.id}")
#     except Exception as e:
#         logger.error(f"Ошибка в process_master_full_name: {str(e)}, user_id={message.from_user.id}")
#         await message.answer("❌ Ошибка при обработке имени. Введите фамилию и имя через пробел (например, Иванов Иван)")
#
#
# @router.message(CreateNewMasterStates.waiting_for_master_work_experience)
# async def process_master_work_experience(message: Message, state: FSMContext):
#     work_experience = message.text.strip()
#     await state.update_data(work_experience=work_experience)
#     await message.answer("Загрузите фото мастера")
#     await state.set_state(CreateNewMasterStates.waiting_for_master_photo)
#
#
# @router.message(CreateNewMasterStates.waiting_for_master_photo, F.photo)
# async def process_master_photo(message: Message, state: FSMContext):
#     async with async_session_maker() as session:
#         try:
#             photo = message.photo[-1]
#             file_id = photo.file_id
#             os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
#             file = await message.bot.get_file(file_id)
#             file_path = file.file_path
#             user_data = await state.get_data()
#             master_last_name = user_data.get("last_name")
#             file_extension = os.path.splitext(file_path)[1]
#             filename = f"master_{master_last_name}{file_extension}"
#             save_path = os.path.join(settings.UPLOAD_FOLDER, filename)
#             await message.bot.download_file(file_path, save_path)
#             master_data = SpecialistCreate(
#                 first_name=user_data.get("first_name"),
#                 last_name=user_data.get("last_name"),
#                 work_experience=user_data.get("work_experience"),
#                 photo=save_path
#             )
#             specialist = await SpecialistServiceClass.create_specialist(session=session, specialist_data=master_data)
#             await message.answer(
#                 f"✅ Мастер успешно добавлен!\n"
#                 f"Имя: {specialist.first_name}\n"
#                 f"Фамилия: {specialist.last_name}\n"
#                 f"Стаж: {specialist.work_experience}\n"
#                 f"Фото: сохранено на сервере",
#                 parse_mode="HTML",
#                 reply_markup=get_admin_functions_kb()
#             )
#         except HTTPException as e:
#             await message.answer(f"❌ Ошибка: {e.detail}", reply_markup=get_admin_functions_kb())
#         except Exception as e:
#             logger.error(f"Ошибка при добавлении мастера: {str(e)}")
#             await message.answer("❌ Ошибка при добавлении мастера", reply_markup=get_admin_functions_kb())
#         finally:
#             await state.clear()
#
#
# @router.callback_query(F.data == "update_specialist")
# async def handler_update_specialist(callback: CallbackQuery, state: FSMContext):
#     async with async_session_maker() as session:
#         logger.info(f"Вызван handler_update_specialist для user_id={callback.from_user.id}")
#         await callback.answer()
#         specialists = await SpecialistServiceClass.get_specialists(session=session)
#         if not specialists:
#             await callback.message.answer("ℹ️ Список специалистов пуст")
#             logger.info(f"Список специалистов пуст для user_id={callback.from_user.id}")
#             return
#
#         await callback.message.answer(
#             "Выберите специалиста для обновления",
#             reply_markup=get_masters_list_kb(specialists)
#         )
#         await state.set_state(UpdateMasterStates.waiting_for_specialist_id_to_update)
#         logger.info(f"Установлено состояние waiting_for_specialist_id_to_update для user_id={callback.from_user.id}")
#
#
# @router.callback_query(UpdateMasterStates.waiting_for_specialist_id_to_update, F.data.startswith("master_"))
# async def process_specialist_id_to_update(callback: CallbackQuery, state: FSMContext):
#     async with async_session_maker() as session:
#         try:
#             specialist_id = int(callback.data.replace("master_", ""))
#             specialist = await SpecialistServiceClass.get_specialist(session=session, specialist_id=specialist_id)
#             await state.update_data(specialist_id=specialist_id, last_name=specialist.last_name)
#             await callback.message.answer(
#                 f"Специалист найден:\n\n"
#                 f"ID: {specialist.id}\n"
#                 f"Имя: {specialist.first_name}\n"
#                 f"Фамилия: {specialist.last_name}\n"
#                 f"Стаж: {specialist.work_experience or 'Не указан'}\n"
#                 f"Фото: {specialist.photo or 'Не загружено'}\n\n"
#                 "Выберите поле для изменения:",
#                 reply_markup=get_specialist_fields_kb()
#             )
#             await state.set_state(UpdateMasterStates.waiting_for_specialist_field_to_update)
#             logger.info(f"Выбран специалист ID={specialist_id} для обновления, user_id={callback.from_user.id}")
#         except ValueError:
#             await callback.message.answer("⚠️ Пожалуйста, выберите корректный ID специалиста")
#             logger.error(f"Некорректный ID специалиста в callback.data={callback.data}, user_id={callback.from_user.id}")
#         except HTTPException as e:
#             await callback.message.answer(f"❌ Ошибка: {e.detail}", reply_markup=get_admin_functions_kb())
#             logger.error(f"HTTPException при выборе специалиста: {e.detail}, user_id={callback.from_user.id}")
#         except Exception as e:
#             logger.error(f"Ошибка при выборе специалиста: {str(e)}, user_id={callback.from_user.id}")
#             await callback.message.answer("❌ Произошла ошибка при выборе специалиста",
#                                          reply_markup=get_admin_functions_kb())
#         await callback.answer()
#
#
# @router.callback_query(UpdateMasterStates.waiting_for_specialist_field_to_update)
# async def process_specialist_field_to_update(callback: CallbackQuery, state: FSMContext):
#     field_action = callback.data
#     field_map = {
#         "update_specialist_first_name": "новое имя",
#         "update_specialist_last_name": "новую фамилию",
#         "update_specialist_work_experience": "новый стаж работы (например, 5 лет)",
#         "update_specialist_photo": "новое фото"
#     }
#
#     await state.update_data(field_to_update=field_action)
#     if field_action == "update_specialist_photo":
#         await callback.message.answer(
#             "Загрузите новое фото специалиста:",
#         )
#     else:
#         await callback.message.answer(
#             f"Введите {field_map.get(field_action, 'значение')}:",
#         )
#     await callback.answer()
#     await state.set_state(UpdateMasterStates.waiting_for_specialist_new_value)
#     logger.info(f"Выбрано поле для обновления: {field_action}, user_id={callback.from_user.id}")
#
#
# @router.message(UpdateMasterStates.waiting_for_specialist_new_value, F.text | F.photo)
# async def process_specialist_new_value(message: Message, state: FSMContext):
#     async with async_session_maker() as session:
#         try:
#             data = await state.get_data()
#             specialist_id = data['specialist_id']
#             field = data['field_to_update']
#             update_data = SpecialistUpdate()
#
#             if field == "update_specialist_photo":
#                 if not message.photo:
#                     await message.answer("❌ Пожалуйста, загрузите фото")
#                     logger.warning(f"Ожидалось фото, получен текст: {message.text}, user_id={message.from_user.id}")
#                     return
#                 photo = message.photo[-1]
#                 file_id = photo.file_id
#                 os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
#                 file = await message.bot.get_file(file_id)
#                 file_path = file.file_path
#                 file_extension = os.path.splitext(file_path)[1]
#                 master_last_name = data.get("last_name")
#                 if not master_last_name:
#                     master_last_name = f"id_{specialist_id}"
#                     logger.warning(f"last_name не найден в state, использую specialist_id={specialist_id}, user_id={message.from_user.id}")
#                 filename = f"master_{master_last_name}{file_extension}"
#                 save_path = os.path.join(settings.UPLOAD_FOLDER, filename)
#                 await message.bot.download_file(file_path, save_path)
#                 update_data.photo = save_path
#             else:
#                 if not message.text:
#                     await message.answer("❌ Пожалуйста, введите текстовое значение")
#                     logger.warning(f"Ожидался текст, получено фото, user_id={message.from_user.id}")
#                     return
#                 new_value = message.text.strip()
#                 if field == "update_specialist_first_name":
#                     update_data.first_name = new_value
#                 elif field == "update_specialist_last_name":
#                     update_data.last_name = new_value
#                 elif field == "update_specialist_work_experience":
#                     update_data.work_experience = new_value
#
#             updated_specialist = await SpecialistServiceClass.update_specialist(
#                 session=session,
#                 specialist_id=specialist_id,
#                 specialist_data=update_data
#             )
#             await message.answer(
#                 f"✅ Специалист успешно обновлён!\n\n"
#                 f"ID: {updated_specialist.id}\n"
#                 f"Имя: {updated_specialist.first_name}\n"
#                 f"Фамилия: {updated_specialist.last_name}\n"
#                 f"Стаж: {updated_specialist.work_experience or 'Не указан'}\n"
#                 f"Фото: {updated_specialist.photo or 'Не загружено'}",
#                 reply_markup=get_admin_functions_kb()
#             )
#             logger.info(f"Specialist {specialist_id} updated. Changes: {update_data.model_dump()}, user_id={message.from_user.id}")
#         except HTTPException as e:
#             await message.answer(f"❌ Ошибка: {e.detail}")
#             logger.error(f"HTTPException при обновлении специалиста: {e.detail}, user_id={message.from_user.id}")
#         except Exception as e:
#             logger.error(f"Ошибка при обновлении специалиста: {str(e)}, user_id={message.from_user.id}")
#             await message.answer("❌ Произошла ошибка при обновлении специалиста")
#         finally:
#             await state.clear()
#
#
# @router.callback_query(F.data == "add_new_service_to_master")
# async def handler_add_new_service_to_master(callback: CallbackQuery, state: FSMContext):
#     try:
#         async with async_session_maker() as session:
#             masters = await SpecialistDAO.find_all(session=session)
#             if not masters:
#                 await callback.message.answer("❌ Нет доступных мастеров")
#                 return
#
#             await callback.answer()
#             await callback.message.answer(
#                 "👨‍💼 Выберите мастера, которому хотите добавить услугу:",
#                 reply_markup=get_masters_list_kb(masters)
#             )
#             await state.set_state(AddToMasterServiceStates.waiting_for_master_id)
#             await callback.answer()
#
#     except Exception as e:
#         logger.error(f"Error in handler_add_new_service_to_master: {e}")
#         await callback.message.answer("❌ Ошибка при получении списка мастеров")
#
#
# @router.callback_query(AddToMasterServiceStates.waiting_for_master_id, F.data.startswith("master_"))
# async def process_master_id(callback: CallbackQuery, state: FSMContext):
#     master_id = int(callback.data.replace("master_", ""))
#     await state.update_data(master_id=master_id)
#     try:
#         async with async_session_maker() as session:
#             services = await ServiceService.get_services(session)
#             if not services:
#                 await callback.message.answer("❌ Услуги не найдены")
#                 return
#
#             await callback.answer()
#             await callback.message.answer(
#                 "Выберите услугу, которую хотите добавить мастеру:",
#                 reply_markup=get_service_list_kb(services)
#             )
#             await state.set_state(AddToMasterServiceStates.waiting_for_service_id)
#             await callback.answer()
#
#     except Exception as e:
#         logger.error(f"Error in handler_add_new_service_to_master: {e}")
#         await callback.message.answer("❌ Ошибка при получении списка услуг")
#
#
#
# @router.callback_query(AddToMasterServiceStates.waiting_for_service_id, F.data.startswith("service_"))
# async def process_service_id(callback:CallbackQuery, state: FSMContext):
#     async with async_session_maker() as session:
#         try:
#             service_id = int(callback.data.replace("service_", ""))
#             data = await state.get_data()
#             master_id = data.get("master_id")
#             link = await SpecialistServiceClass.add_service_to_specialist(
#                 session=session,
#                 specialist_service=SpecialistServiceCreate(
#                     service_id=service_id,
#                     specialist_id=master_id)
#             )
#             await callback.message.answer(
#                 f"✅ Услуга (ID: {link.service_id}) успешно добавлена мастеру (ID: {link.specialist_id})",
#                 reply_markup=get_admin_functions_kb()
#             )
#         except ValueError:
#             await callback.message.answer("❌ ID должен быть числом. Попробуйте снова.")
#         except HTTPException as e:
#             await callback.message.answer(f"❌ Ошибка: {e.detail}")
#         except Exception as e:
#             logger.error(f"Ошибка при привязке услуги: {str(e)}")
#             await callback.message.answer("❌ Произошла непредвиденная ошибка")
#         finally:
#             await state.clear()
#
#
# @router.callback_query(F.data == "set_schedule")
# async def cmd_set_schedule(callback: CallbackQuery, state: FSMContext):
#     try:
#         async with async_session_maker() as session:
#             masters = await SpecialistServiceClass.get_specialists(session=session)
#             if not masters:
#                 await callback.message.answer("❌ Нет доступных мастеров")
#                 return
#
#             await callback.message.answer(
#                 "👨‍💼 Выберите мастера:",
#                 reply_markup=get_masters_list_kb(masters)
#             )
#             await state.set_state(SetMasterScheduleStates.waiting_for_master_id)
#             await callback.answer()
#
#     except Exception as e:
#         logger.error(f"Ошибка в bot/admin.cmd_set_schedule: {e}")
#         await callback.message.answer("❌ Ошибка при получении списка мастеров")
#
#
# @router.callback_query(SetMasterScheduleStates.waiting_for_master_id, F.data.startswith("master_"))
# async def process_master_selection(callback: CallbackQuery, state: FSMContext):
#     async with async_session_maker() as session:
#         try:
#             master_id = int(callback.data.replace("master_", ""))
#             specialist = await SpecialistServiceClass.get_specialist(session=session, specialist_id=master_id)
#             await state.update_data(master_id=master_id, master_name=f"{specialist.first_name} {specialist.last_name}")
#             await callback.message.answer(text=f"📅 Выберите месяц для настройки расписания "
#                                                f"для мастера {specialist.first_name} {specialist.last_name}",
#                                           reply_markup=get_month_selection_kb())
#
#             await state.set_state(SetMasterScheduleStates.waiting_for_month_selection)
#             await callback.answer()
#         except Exception as e:
#             logger.error(f"Ошибка при выборе мастера: {str(e)}")
#             await callback.message.answer("❌ Ошибка при выборе мастера")
#
#
# @router.callback_query(SetMasterScheduleStates.waiting_for_month_selection, F.data.startswith("month_"))
# async def process_month_selection(callback: CallbackQuery, state: FSMContext):
#     try:
#         month_year = callback.data.replace("month_", "").split("_")
#         target_month, target_year = int(month_year[0]), int(month_year[1])
#         await state.update_data(target_month=target_month, target_year=target_year)
#         data = await state.get_data()
#         await callback.message.answer(
#             f"📅 Выберите дни недели для {data['master_name']} (месяц: {target_month}/{target_year}:\n\n"
#             "✅ - выбран\n⚪ - не выбран",
#             reply_markup=get_days_of_week()
#         )
#         await state.set_state(SetMasterScheduleStates.waiting_for_days_selection)
#         await callback.answer()
#     except Exception as e:
#         logger.error(f"Ошибка при выборе месяца: {str(e)}")
#         await callback.message.anwer("❌ Ошибка при выборе месяца")
#
#
# @router.callback_query(SetMasterScheduleStates.waiting_for_days_selection, F.data.startswith("day_"))
# async def process_day_selection(callback: CallbackQuery, state: FSMContext):
#     try:
#         day_code = callback.data.replace("day_", "")
#         data = await state.get_data()
#         selected_days = data.get("selected_days", set())
#
#         if day_code in selected_days:
#             selected_days.remove(day_code)
#             new_state = False
#         else:
#             selected_days.add(day_code)
#             new_state = True
#
#         await state.update_data(selected_days=selected_days)
#         await callback.message.edit_reply_markup(reply_markup=get_days_of_week(selected_days))
#         await callback.answer(f"{'Выбрано' if new_state else 'Убрано'}")
#     except Exception as e:
#         logger.error(f"Ошибка в process_day_selection: {e}")
#         await callback.answer("❌ Произошла ошибка")
#
#
# @router.callback_query(SetMasterScheduleStates.waiting_for_days_selection, F.data == "select_all_days")
# async def select_all_days(callback: CallbackQuery, state: FSMContext):
#     try:
#         all_days = {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}
#         await state.update_data(selected_days=all_days)
#         await callback.message.edit_reply_markup(reply_markup=get_days_of_week(all_days))
#         await callback.answer("Все дни выбраны")
#     except Exception as e:
#         logger.error(f"Ошибка в select_all_days: {e}")
#         await callback.answer("❌ Произошла ошибка")
#
#
# @router.callback_query(SetMasterScheduleStates.waiting_for_days_selection, F.data == "days_selected")
# async def process_days_confirmation(callback: CallbackQuery, state: FSMContext):
#     try:
#         data = await state.get_data()
#         selected_days = data.get("selected_days", set())
#
#         if not selected_days:
#             await callback.answer("❌ Выберите хотя бы один день")
#             return
#
#         await callback.message.answer(
#             f"📅 Выбранные дни: {len(selected_days)}\n\n"
#             "⏰ Теперь введите время работы в формате:\n"
#             "ЧЧ:ММ-ЧЧ:ММ\n\n"
#             "Пример: 09:00-18:00"
#         )
#         await state.set_state(SetMasterScheduleStates.waiting_for_time_range)
#         await callback.answer()
#
#     except Exception as e:
#         logger.error(f"Ошибка в bot/admin.process_days_confirmation: {e}")
#         await callback.answer("❌ Произошла ошибка")
#
#
# # @router.message(SetMasterScheduleStates.waiting_for_time_range)
# # async def process_time_range(message: Message, state: FSMContext):
# #     if message.text == "❌ Отмена":
# #         await state.clear()
# #         await message.answer("❌ Отменено", reply_markup=get_admin_functions_kb())
# #         return
# #
# #     try:
# #         start_str, end_str = message.text.split("-")
# #         start_time = datetime.strptime(start_str.strip(), "%H:%M").time()
# #         end_time = datetime.strptime(end_str.strip(), "%H:%M").time()
# #
# #         if start_time >= end_time:
# #             await message.answer("❌ Время начала должно быть раньше времени окончания")
# #             return
# #
# #         await state.update_data(start_time=start_time, end_time=end_time)
# #
# #         await message.answer(
# #             "⏱ Выберите интервал между записями:",
# #             reply_markup=get_time_interval_kb()
# #         )
# #         await state.set_state(SetMasterScheduleStates.waiting_for_interval)
# #
# #     except ValueError:
# #         await message.answer("❌ Неверный формат. Используйте ЧЧ:MM-ЧЧ:MM")
#
#
# @router.callback_query(SetMasterScheduleStates.waiting_for_days_selection, F.data == "cancel_schedule")
# async def cancel_schedule(callback: CallbackQuery, state: FSMContext):
#     await state.clear()
#     await callback.message.answer(
#         "❌ Настройка расписания отменена",
#         reply_markup=get_admin_functions_kb()
#     )
#     await callback.answer()
#
#
# # @router.message(SetMasterScheduleStates.waiting_for_interval)
# # async def process_interval(message: Message, state: FSMContext):
# #     if message.text == "❌ Отмена":
# #         await state.clear()
# #         await message.answer("❌ Отменено", reply_markup=get_admin_functions_kb())
# #         return
# #     try:
# #         interval = int(message.text.split()[0])
# #         data = await state.get_data()
# #         # Формируем summary
# #         selected_days = data["selected_days"]
# #         day_names = {
# #             "mon": "Пн", "tue": "Вт", "wed": "Ср", "thu": "Чт",
# #             "fri": "Пт", "sat": "Сб", "sun": "Вс"
# #         }
# #         days_str = ", ".join([day_names[day] for day in selected_days])
# #
# #         summary = (
# #             f"📋 Подтвердите настройки:\n\n"
# #             f"👨‍💼 Мастер: {data['master_name']}\n"
# #             f"📅 Дни: {days_str}\n"
# #             f"⏰ Время: {data['start_time'].strftime('%H:%M')}-{data['end_time'].strftime('%H:%M')}\n"
# #             f"⏱ Интервал: {interval} минут\n\n"
# #             f"Будет {'обновлено' if data['target_month'] == datetime.now().month else 'создано'} расписание."
# #         )
# #
# #         await state.update_data(interval=interval)
# #         await message.answer(summary, reply_markup=get_confirmation_kb())
# #         await state.set_state(SetMasterScheduleStates.waiting_for_confirmation)
# #     except (ValueError, IndexError):
# #         await message.answer("❌ Неверный формат. Выберите интервал из списка")
#
#
# @router.message(SetMasterScheduleStates.waiting_for_confirmation)
# async def process_confirmation(message: Message, state: FSMContext):
#     async with async_session_maker() as session:
#         try:
#             if message.text != "✅ Подтвердить":
#                 await message.answer("❌ Используйте кнопки для подтверждения")
#                 return
#             data = await state.get_data()
#             schedule_dao = ScheduleDAO()
#             if data['target_month'] == datetime.now().month and data['target_year'] == datetime.now().year:
#                 # обновление текущего месяца
#                 schedules = await schedule_dao.update_monthly_schedule(
#                     session=session,
#                     specialist_id=data["master_id"],
#                     working_days=list(data["selected_days"]),
#                     start_time=data["start_time"],
#                     end_time=data["end_time"],
#                     slot_duration_minutes=data["interval"],
#                     target_month=data["target_month"],
#                     target_year=data["target_year"]
#                 )
#                 action = "обновлено"
#             else:
#                 # создание для будущего месяца
#                 schedules = await schedule_dao.generate_monthly_schedule(
#                     session=session,
#                     specialist_id=data["master_id"],
#                     working_days=list(data["selected_days"]),
#                     start_time=data["start_time"],
#                     end_time=data["end_time"],
#                     slot_duration_minutes=data["interval"],
#                     target_month=data["target_month"],
#                     target_year=data["target_year"]
#                 )
#                 action = "создано"
#
#             await message.answer(
#                 f"✅ Расписание успешно {action}!\n"
#                 f"Обработано {len(schedules)} рабочих дней",
#                 reply_markup=get_admin_functions_kb()
#             )
#         except HTTPException as e:
#             await message.answer(f"❌ Ошибка: {e.detail}")
#         except Exception as e:
#             logger.error(f"Ошибка при создании/обновлении расписания: {str(e)}")
#             await message.answer("❌ Ошибка при обработке расписания")
#         finally:
#             await state.clear()