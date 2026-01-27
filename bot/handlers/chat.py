from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from core.services import ConsultationService

router = Router()

@router.message(Command("finish"))
async def finish_chat(message: Message, service: ConsultationService):
    """Команда для завершения консультации"""
    partner_id = await service.finish_consultation(message.from_user.id)
    
    if partner_id:
        # Уведомляем того, кто нажал
        await message.answer("✅ Консультация завершена.")
        # Уведомляем собеседника
        await message.bot.send_message(partner_id, "✅ Собеседник завершил консультацию.")
    else:
        await message.answer("У вас нет активной консультации.")

@router.message()
async def forward_message(message: Message, service: ConsultationService):
    """
    Магия пересылки. Ловит ЛЮБОЕ сообщение (текст, фото, голос).
    """
    # 1. Проверяем, есть ли активная консультация
    partner_id = await service.get_active_partner(message.from_user.id)

    if partner_id:
        # 2. Если есть - копируем сообщение собеседнику
        # send_copy - идеальный метод: он копирует и текст, и фото, и голосовые
        await message.send_copy(chat_id=partner_id)
    else:
        # 3. Если нет консультации - игнорируем или говорим, что делать
        # (чтобы не спамить, можно отвечать только на текст)
        if message.text:
            await message.answer("Вы не находитесь в активном чате. Нажмите /start или /doctor_mode")