from aiogram.fsm.state import State, StatesGroup

class PatientStates(StatesGroup):
    initial_symptom = State()
    answering_questions = State()
    choosing_consultation = State()