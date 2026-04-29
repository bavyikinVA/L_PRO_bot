from aiogram.fsm.state import StatesGroup, State


class AdminStates(StatesGroup):
    waiting_for_service_name = State()
    waiting_for_service_description = State()
    waiting_for_service_price = State()
    waiting_for_service_id_to_update = State()
    waiting_for_service_field_to_update = State()
    waiting_for_service_new_value = State()


class CreateNewUserStates(StatesGroup):
    waiting_for_user_full_name = State()
    waiting_for_user_phone_number = State()
    waiting_for_tg_id = State()
    waiting_for_tg_username = State()
    waiting_for_user_admin_state = State()


class CreateNewMasterStates(StatesGroup):
    waiting_for_master_full_name = State()
    waiting_for_master_work_experience = State()
    waiting_for_master_photo = State()


class UpdateMasterStates(StatesGroup):
    waiting_for_specialist_id_to_update = State()
    waiting_for_specialist_field_to_update = State()
    waiting_for_specialist_new_value = State()


class AddToMasterServiceStates(StatesGroup):
    waiting_for_master_id = State()
    waiting_for_service_id = State()


class SetMasterScheduleStates(StatesGroup):
    waiting_for_master_id = State()
    waiting_for_month_selection = State()
    waiting_for_days_selection = State()
    waiting_for_time_range = State()
    waiting_for_interval = State()
    waiting_for_confirmation = State()