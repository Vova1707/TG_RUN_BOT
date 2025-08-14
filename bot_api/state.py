from aiogram.fsm.state import StatesGroup, State

class JoggingState(StatesGroup):

    set_jogging_data = State()
    set_jogging_time = State()
    set_photo = State()