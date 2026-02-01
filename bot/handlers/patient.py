import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from bot.states import PatientStates
from bot.keyboards.patient import get_start_keyboard, get_symptoms_keyboard
from core.services import ConsultationService
from bot.navigation import set_user_menu

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, service: ConsultationService):
    await state.clear()
    
    # 1. Получаем ID главного админа из настроек (.env)
    admin_id = int(os.getenv("ADMIN_ID", 0))
    current_id = message.from_user.id
    
    # 2. Определяем роль: Если это Вы — то "admin", иначе "patient"
    initial_role = "admin" if current_id == admin_id else "patient"

    # 3. Регистрируем пользователя
    user = await service.create_user_if_not_exists(
        telegram_id=current_id,
        username=message.from_user.username,
        role=initial_role,
        full_name=message.from_user.full_name
    )

    # 4. --- ПРИНУДИТЕЛЬНОЕ ОБНОВЛЕНИЕ ДЛЯ АДМИНА ---
    # Если вы уже есть в базе как "patient", код выше не изменит роль.
    # Поэтому заставляем базу вспомнить, кто тут босс.
    if current_id == admin_id and user.role != "admin":
        await service.set_user_role(current_id, "admin")
        user.role = "admin" # Обновляем переменную для меню
    # -----------------------------------------------

    # 5. Выдаем правильное меню (Админское или Обычное)
    await set_user_menu(message.bot, current_id, user.role)

    text = "👋 **Добро пожаловать в DoctorDirect!**\nНажмите кнопку ниже, чтобы начать."
    if user.role == "admin":
        text = "👑 **Добро пожаловать, Создатель!**\nВы авторизованы как Администратор."

    await message.answer(
        text,
        reply_markup=get_start_keyboard()
    )

# 2. НАЖАТИЕ КНОПКИ "НАЧАТЬ"
@router.callback_query(F.data == "start_triage")
async def start_triage_flow(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text("✍️ Шаг 1: Опишите, что вас беспокоит?")
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

# 5. ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ
async def ask_for_decision(message: Message, state: FSMContext, history: list):
    ai = AIService()
    summary = await ai.analyze_anamnesis(history)
    
    full_report = "\n".join(history) + "\n\n" + summary
    await state.update_data(full_report=full_report)
    
    # Убрали Markdown. Теперь бот не сломается, если AI напишет странный символ.
    await message.answer(
        f"✅ Опрос завершен. Предварительный анализ:\n\n"
        f"{summary}\n\n"
        f"Хотите передать эту информацию живому врачу для консультации?",
        reply_markup=get_consultation_choice_keyboard()
    )
    await state.set_state(PatientStates.choosing_consultation)

# 6. ЕСЛИ НАЖАЛ "НУЖЕН ВРАЧ"
@router.callback_query(F.data == "req_doctor", PatientStates.choosing_consultation)
async def confirm_doctor(callback: CallbackQuery, state: FSMContext, service: ConsultationService):
    data = await state.get_data()
    full_report = data.get("full_report", "Ошибка данных")
    
    # Обновляем данные (вдруг юзер сменил имя пока проходил опрос)
    await service.create_user_if_not_exists(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        role="patient",
        full_name=callback.from_user.full_name
    )
    
    cons_id = await service.add_to_queue(callback.from_user.id, full_report)
    
    await callback.message.edit_text(
        f"✅ Заявка #{cons_id} отправлена!\nОжидайте подключения врача."
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
