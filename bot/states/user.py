from aiogram.fsm.state import StatesGroup, State


class UserStates(StatesGroup):
    waiting_for_user_full_name = State()
    waiting_for_user_phone_number = State()
    waiting_for_tg_id = State()
    waiting_for_tg_username = State()
    waiting_for_user_admin_state = State()