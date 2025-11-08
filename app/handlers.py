# handlers.py
import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command
from aiogram.enums import ChatAction
from aiogram.fsm.context import FSMContext

from app import keyboards as kb
from app import states as st
from app.data import *

router = Router()

async def typing(message: Message):
    await message.bot.send_chat_action(chat_id=message.from_user.id, action=ChatAction.TYPING)

@router.message(F.text == 'check')
async def check(message: Message):
    await message.answer('na suka')

@router.message(CommandStart())
async def start(message: Message):
    await typing(message=message)
    await asyncio.sleep(0.35)
    await message.answer(
        text=f'Здравствуйте, {message.from_user.first_name}, это нейро-врач healthGPT,\nВыберите из списка ваше амплуа',
        reply_markup=kb.main
    )

# Пациент
@router.callback_query(F.data == 'patient')
async def patient(callback: CallbackQuery, state: FSMContext):
    await state.set_state(st.AuthP.fio)
    await callback.message.edit_text(text='Скажите, как к вам обращаться')

@router.message(st.AuthP.fio)
async def auth_fio(message: Message, state: FSMContext):
    await state.update_data(fio=message.text)
    await state.set_state(st.AuthP.age)
    await message.answer(text='Скажите ваш год рождения')

@router.message(st.AuthP.age)
async def auth_age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    data_patient = await state.get_data()
    
    # Регистрируем пациента
    add_user(message.from_user.id, UserRole.PATIENT, data_patient)
    patient_data[message.from_user.id] = {
        "fio": data_patient['fio'],
        "age": data_patient['age'],
        "messages": []
    }
    
    await state.set_state(st.Appeal.appeal1)
    await message.answer(text='Скажите, что вас беспокоит?')

@router.message(st.Appeal.appeal1)
async def appeal_1(message: Message, state: FSMContext):
    appeal_text = message.text
    await state.update_data(appeal1=appeal_text)
    
    # Сохраняем обращение
    if message.from_user.id not in patient_data:
        patient_data[message.from_user.id] = {"messages": []}
    
    patient_data[message.from_user.id]["messages"].append({
        "role": "patient",
        "text": appeal_text
    })
    
    # Имитация нейросети - задаем уточняющие вопросы
    await state.set_state(st.Appeal.questions)
    questions = [
        "Как давно у вас появились эти симптомы?",
        "Насколько интенсивны эти симптомы по шкале от 1 до 10?",
        "Что провоцирует ухудшение состояния?",
        "Что облегчает ваше состояние?"
    ]
    
    # Сохраняем вопросы нейросети
    for question in questions[:2]:  # Первые 2 вопроса
        patient_data[message.from_user.id]["messages"].append({
            "role": "bot",
            "text": question
        })
    
    await message.answer("Нейросеть задает уточняющие вопросы:")
    for question in questions[:2]:
        await asyncio.sleep(1)
        await message.answer(question)
    
    await message.answer("Пожалуйста, ответьте на эти вопросы по очереди:")

@router.message(st.Appeal.questions)
async def process_questions(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    # Сохраняем ответ пациента
    patient_data[user_id]["messages"].append({
        "role": "patient",
        "text": message.text
    })
    
    # Проверяем, достаточно ли ответов
    if len([m for m in patient_data[user_id]["messages"] if m["role"] == "patient"]) >= 3:
        # Формируем предварительный ответ
        await message.answer(
            "По описанию у вас может быть... (предварительный диагноз). "
            "Рекомендуется консультация с врачом для уточнения."
        )
        
        # Спрашиваем, хочет ли пациент консультацию
        await state.set_state(st.Appeal.consultation_choice)
        await message.answer(
            "Хотели бы вы получить консультацию с врачом?",
            reply_markup=kb.consultation_choice
        )

# Обработка выбора консультации
@router.callback_query(st.Appeal.consultation_choice, F.data.in_(['request_consultation', 'no_consultation']))
async def handle_consultation_choice(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    
    if callback.data == 'request_consultation':
        # Добавляем в очередь
        add_to_queue(user_id)
        await callback.message.edit_text(
            "Вы добавлены в очередь на консультацию. Ожидайте подключения врача."
        )
        
        # Уведомляем врачей о новом пациенте
        await notify_doctors(callback.bot, user_id)
    else:
        await callback.message.edit_text(
            "Спасибо, что воспользовались нашим ботом! Если что-то заболит, обращайтесь!"
        )
    
    await state.clear()

async def notify_doctors(bot, patient_id):
    """Уведомляет всех врачей о новом пациенте с полной историей переписки"""
    for user_id, user_data in users.items():
        if user_data["role"] == UserRole.DOCTOR and not is_in_consultation(user_id):
            try:
                patient_info = patient_data[patient_id]
                messages = patient_info["messages"]
                
                # Формируем полную историю переписки для уведомления
                text = "🆕 Новый пациент в очереди:\n\n"
                
                # Добавляем информацию о пациенте
                if "fio" in patient_info:
                    text += f"👤 Пациент: {patient_info['fio']}\n"
                if "age" in patient_info:
                    text += f"🎂 Год рождения: {patient_info['age']}\n"
                text += "\n" + "="*50 + "\n\n"
                
                # Добавляем всю переписку
                for i, msg in enumerate(messages, 1):
                    if msg["role"] == "patient":
                        role_text = "👤 Пациент"
                    elif msg["role"] == "bot":
                        role_text = "🤖 Бот"
                    else:
                        role_text = "❓ Неизвестно"
                    
                    text += f"{i}. {role_text}:\n{msg['text']}\n\n"
                    text += "-" * 30 + "\n\n"
                
                # Если текст слишком длинный, обрезаем но оставляем основное
                if len(text) > 4000:
                    text = text[:4000] + "\n\n... (переписка продолжается)"
                
                await bot.send_message(
                    user_id,
                    text=text,
                    reply_markup=kb.accept_consultation
                )
            except Exception as e:
                print(f"Ошибка уведомления врача {user_id}: {e}")

# Врач
@router.callback_query(F.data == 'doctor')
async def doc1(callback: CallbackQuery):
    await callback.message.edit_text(
        text='Если вы зарегистрированы, авторизуйтесь, в противном случае - зарегистрируйтесь', 
        reply_markup=kb.reg_authorise
    )

@router.callback_query(F.data == 'regist')
async def RegD(callback: CallbackQuery):
    await callback.message.edit_text(text='Свяжитесь с дежурным администратором для регистрации\n @ALEXADLLL')

@router.callback_query(F.data == "authorise")
async def AuthDoc(callback: CallbackQuery, state: FSMContext):
    await state.set_state(st.AuthD.fio)
    await callback.message.edit_text(text="Введите ваше ФИО")

@router.message(st.AuthD.fio)
async def AuthDoc_fio(message: Message, state: FSMContext):
    await state.update_data(fio=message.text)
    await state.set_state(st.AuthD.number)
    await message.answer(text='Введите номер телефона', reply_markup=kb.telnum)

@router.message(st.AuthD.number, F.contact)
async def AuthDoc_num(message: Message, state: FSMContext):
    await state.update_data(number=message.contact.phone_number)
    data = await state.get_data()
    
    # Регистрируем врача
    add_user(message.from_user.id, UserRole.DOCTOR, data)
    
    await state.clear()
    await message.answer(
        text=f"Авторизация завершена,\nВаше ФИО: {data['fio']},\nВаш номер телефона: {data['number']}", 
        reply_markup=ReplyKeyboardRemove()
    )

@router.callback_query(F.data == 'accept_consultation')
async def accept_consultation(callback: CallbackQuery):
    doctor_id = callback.from_user.id
    
    # Получаем следующего пациента из очереди
    patient_id = get_next_patient()
    
    if patient_id:
        # Начинаем консультацию
        start_consultation(patient_id, doctor_id)
        
        # Отправляем всю историю переписки врачу
        patient_info = patient_data[patient_id]
        messages = patient_info["messages"]
        
        # Формируем полную историю переписки
        text = "Полная история переписки с пациентом:\n\n"
        
        # Добавляем информацию о пациенте
        if "fio" in patient_info:
            text += f"Пациент: {patient_info['fio']}\n"
        if "age" in patient_info:
            text += f"Год рождения: {patient_info['age']}\n"
        text += "\n" + "="*50 + "\n\n"
        
        # Добавляем все сообщения из переписки
        for i, msg in enumerate(messages, 1):
            if msg["role"] == "patient":
                role_text = "👤 Пациент"
            elif msg["role"] == "bot":
                role_text = "🤖 Бот"
            else:
                role_text = "❓ Неизвестно"
            
            text += f"{i}. {role_text}:\n{msg['text']}\n\n"
            text += "-" * 30 + "\n\n"
        
        # Если переписка очень длинная, разбиваем на несколько сообщений
        if len(text) > 4000:
            # Разбиваем текст на части по ~4000 символов
            parts = []
            while len(text) > 4000:
                # Находим место разрыва по последнему переносу строки
                break_point = text[:4000].rfind('\n\n')
                if break_point == -1:
                    break_point = 4000
                parts.append(text[:break_point])
                text = text[break_point:].strip()
            parts.append(text)
            
            # Отправляем первую часть с заголовком
            await callback.message.edit_text(
                text=parts[0],
                reply_markup=kb.consultation_keyboard
            )
            
            # Отправляем остальные части как отдельные сообщения
            for part in parts[1:]:
                await callback.message.answer(part)
        else:
            # Если переписка короткая, отправляем одним сообщением
            await callback.message.edit_text(
                text=text + "Теперь вы можете общаться с пациентом.",
                reply_markup=kb.consultation_keyboard
            )
        
        # Уведомляем пациента
        await callback.bot.send_message(
            patient_id,
            "✅ С вами свяжется врач. Теперь вы можете общаться напрямую."
        )
        
        # Также отправляем краткое уведомление врачу о начале консультации
        await callback.message.answer(
            f"✅ Консультация с пациентом начата. Вы можете начать общение.",
            reply_markup=kb.consultation_start
        )
    else:
        await callback.answer("Нет пациентов в очереди")

@router.callback_query(F.data == 'reject_consultation')
async def reject_consultation(callback: CallbackQuery):
    await callback.message.edit_text("Вы отклонили консультацию.")

# Обработка сообщений во время консультации
@router.message()
async def consultation_message(message: Message):
    user_id = message.from_user.id
    
    # Проверяем, находится ли пользователь в консультации
    if not is_in_consultation(user_id):
        # Если не в консультации, игнорируем сообщение или обрабатываем как-то иначе
        return
    
    partner_id = get_consultation_partner(user_id)
    
    if not partner_id:
        await message.answer("Консультация завершена")
        return
    
    # Определяем роль отправителя
    if user_id in active_consultations:  # Пациент
        sender_role = "Пациент"
    else:  # Врач
        sender_role = "Врач"
    
    # Пересылаем сообщение
    await message.bot.send_message(
        partner_id,
        f"{sender_role}: {message.text}"
    )
    
    # Сохраняем в истории
    if user_id in patient_data:
        patient_data[user_id]["messages"].append({
            "role": "patient" if sender_role == "Пациент" else "doctor",
            "text": message.text
        })

@router.callback_query(F.data == 'end_consultation')
async def end_consultation_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    partner_id = get_consultation_partner(user_id)
    
    if partner_id:
        # Определяем ID пациента (консультация всегда связана с пациентом)
        patient_id = partner_id if user_id not in active_consultations else user_id
        end_consultation(patient_id)
        
        await callback.message.edit_text("Консультация завершена")
        await callback.bot.send_message(partner_id, "Врач завершил консультацию")
    
# Админ
@router.callback_query(F.data == 'admin')
async def admin_access(callback: CallbackQuery, state: FSMContext):
    # Здесь должна быть проверка прав доступа
    await state.set_state(st.AdminStates.wait_command)
    await callback.message.edit_text(
        text="Панель администратора",
        reply_markup=kb.admin_keyboard
    )

@router.callback_query(F.data == 'admin_stats')
async def admin_stats(callback: CallbackQuery):
    stats_text = f"""
Статистика:
- Пациентов в очереди: {len(patients_queue)}
- Активных консультаций: {len(active_consultations)}
- Всего пользователей: {len(users)}
"""
    await callback.message.edit_text(text=stats_text, reply_markup=kb.admin_keyboard)

@router.callback_query(F.data == 'admin_exit')
async def admin_exit(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        text="Вы вышли из панели администратора.",
        reply_markup=kb.main
    )