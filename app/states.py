from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext



class AuthD(StatesGroup):
    fio = State()
    number = State()

class AuthP(StatesGroup):
    fio = State()
    age = State()

class Appeal(StatesGroup):
    appeal1 = State()
    questions = State()  # Для уточняющих вопросов
    consultation_choice = State()  # Новое состояние для выбора консультации

class AdminStates(StatesGroup):
    wait_command = State()

