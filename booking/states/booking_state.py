from aiogram.fsm.state import State, StatesGroup


class BookingState(StatesGroup):
    waiting_for_date = State()
    waiting_for_time = State()
    waiting_for_guests = State()
    waiting_for_preference = State()
