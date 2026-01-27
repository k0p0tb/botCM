from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from core.services import ConsultationService
from core.ai_service import AIService
from bot.keyboards.patient import get_start_keyboard, get_consultation_choice_keyboard

router = Router()

# ВОТ ТУТ БЫЛА ОШИБКА. Убедитесь, что добавлены ВСЕ три строчки:
class PatientStates(StatesGroup):
    initial_symptom = State()
    answering_questions = State()
    choosing_consultation = State() # <--- ВЫ ЗАБЫЛИ ВОТ ЭТУ СТРОЧКУ

# 1. ПРИХОЖАЯ
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 **Добро пожаловать в DoctorDirect!**\nНажмите кнопку ниже, чтобы начать.",
        reply_markup=get_start_keyboard(),
        parse_mode="Markdown"
    )

# 2. НАЖАТИЕ КНОПКИ "НАЧАТЬ"
@router.callback_query(F.data == "start_triage")
async def start_triage_flow(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text("✍️ **Шаг 1:** Опишите, что вас беспокоит?")
    await state.set_state(PatientStates.initial_symptom)

# 3. ПОЛУЧАЕМ ПЕРВУЮ ЖАЛОБУ
@router.message(PatientStates.initial_symptom)
async def process_initial_symptom(message: Message, state: FSMContext):
    history = [f"Жалоба: {message.text}"]
    await state.update_data(history=history)
    
    ai = AIService()
    first_q = await ai.get_next_question(history)
    
    if first_q:
        await message.answer(f"🤖 {first_q}")
        await state.set_state(PatientStates.answering_questions)
    else:
        await ask_for_decision(message, state, history)

# 4. ЦИКЛ ОПРОСА
@router.message(PatientStates.answering_questions)
async def process_interview(message: Message, state: FSMContext):
    data = await state.get_data()
    history = data.get('history', [])
    history.append(f"Ответ: {message.text}")
    
    ai = AIService()
    next_q = await ai.get_next_question(history)
    
    if next_q:
        await state.update_data(history=history)
        await message.answer(f"🤖 {next_q}")
    else:
        await ask_for_decision(message, state, history)

# 5. ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ: ПОКАЗ РЕЗУЛЬТАТА И КНОПОК
async def ask_for_decision(message: Message, state: FSMContext, history: list):
    ai = AIService()
    summary = await ai.analyze_anamnesis(history)
    
    full_report = "\n".join(history) + "\n\n" + summary
    await state.update_data(full_report=full_report)
    
    await message.answer(
        f"✅ **Опрос завершен. Предварительный анализ:**\n\n"
        f"{summary}\n\n"
        f"Хотите передать эту информацию живому врачу для консультации?",
        reply_markup=get_consultation_choice_keyboard(),
        parse_mode="Markdown"
    )
    # Переходим в режим выбора
    await state.set_state(PatientStates.choosing_consultation)

# 6. ЕСЛИ НАЖАЛ "НУЖЕН ВРАЧ"
@router.callback_query(F.data == "req_doctor", PatientStates.choosing_consultation)
async def confirm_doctor(callback: CallbackQuery, state: FSMContext, service: ConsultationService):
    data = await state.get_data()
    full_report = data.get("full_report", "Ошибка данных")
    
    await service.create_user_if_not_exists(callback.from_user.id, "patient", callback.from_user.full_name)
    cons_id = await service.add_to_queue(callback.from_user.id, full_report)
    
    await callback.message.edit_text(
        f"✅ **Заявка #{cons_id} отправлена!**\n"
        f"Ожидайте подключения врача.",
        parse_mode="Markdown"
    )
    await state.clear()

# 7. ЕСЛИ НАЖАЛ "НЕ НАДО"
@router.callback_query(F.data == "no_doctor", PatientStates.choosing_consultation)
async def decline_doctor(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Хорошо. Надеюсь, рекомендации AI были полезны.\n"
        "Будьте здоровы! Нажмите /start если снова понадобится помощь."
    )
    await state.clear()

# 8. ЗАГЛУШКА ДЛЯ ЛИШНИХ СООБЩЕНИЙ
@router.message()
async def unknown_message(message: Message):
    if message.text.startswith("/"):
        return
    await message.answer(
        "⛔ Я сейчас не веду запись.\n"
        "Нажмите **/start**, чтобы открыть меню.",
        parse_mode="Markdown"
    )