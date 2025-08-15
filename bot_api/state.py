from aiogram.fsm.state import StatesGroup, State


class User(StatesGroup):
    chose_action = State()
    get_coordinates = State()
    confirm_coordinates = State()
    over = State()

    class CreateJoggingState(StatesGroup):
        set_description = State()
        set_date = State()
        set_time = State()
        ans_photo = State()
        set_photo = State()

    class PathJoggingState(StatesGroup):
        set_distance = State()
        get_path = State()

    class JoinJoggingState(StatesGroup):
        run_search = State()