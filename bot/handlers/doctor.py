from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from core.services import ConsultationService

router = Router()

@router.message(Command("doctor_mode"))
async def doctor_login(message: Message, service: ConsultationService):
    # Регистрируем как врача (для теста)
    await service.create_user_if_not_exists(message.from_user.id, "doctor", message.from_user.full_name)
    await message.answer("Вы авторизованы как врач. Нажмите /queue чтобы видеть пациентов.")

@router.message(Command("queue"))
async def show_queue(message: Message, service: ConsultationService):
    queue = await service.get_queue()
    if not queue:
        await message.answer("Очередь пуста.")
        return
    
    text = "Ожидающие пациенты:\n"
    kb = []
    for consult in queue:
        text += f"ID: {consult.id}. Симптомы: {consult.symptoms[:50]}...\n"
        kb.append([InlineKeyboardButton(text=f"Принять #{consult.id}", callback_data=f"accept_{consult.id}")])
    
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@router.callback_query(F.data.startswith("accept_"))
async def accept_patient(callback: CallbackQuery, service: ConsultationService):
    cons_id = int(callback.data.split("_")[1])
    
    # АТОМАРНАЯ ПРОВЕРКА
    success = await service.assign_doctor(cons_id, callback.from_user.id)
    
    if success:
        await callback.message.edit_text(f"✅ Вы взяли пациента по заявке #{cons_id}. Можно начинать чат.")
        # Тут можно отправить уведомление пациенту через bot.send_message
    else:
        await callback.message.edit_text("⚠️ Эту заявку уже перехватил другой врач.")