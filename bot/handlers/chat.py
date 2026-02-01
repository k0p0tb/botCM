import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from core.services import ConsultationService
from sqlalchemy.ext.asyncio import AsyncSession
from database.base import async_session

router = Router()

# --- ЛОГИКА ТАЙМЕРА ---
async def wait_and_finish(consultation_id: int, bot: Bot):
    """Ждет 5 минут (300 сек) и завершает, если пациент не ответил."""
    await asyncio.sleep(300)  # 300 секунд = 5 минут

    async with async_session() as session:
        service = ConsultationService(session)
        consultation = await service.get_consultation_status(consultation_id)
        
        # Если консультация всё еще активна И метка времени не исчезла
        if consultation and consultation.status == "active" and consultation.finish_requested_at:
            # Принудительно завершаем
            await service.finish_consultation(consultation.doctor_id)
            
            # Уведомляем обоих
            try:
                await bot.send_message(consultation.patient_id, "⏳ Время ожидания истекло. Консультация завершена.")
                await bot.send_message(consultation.doctor_id, "✅ Пациент не ответил. Консультация завершена автоматически.")
            except:
                pass

# ----------------------

@router.message(Command("finish"))
async def request_finish_chat(message: Message, service: ConsultationService):
    """Врач запрашивает завершение"""
    # 1. Ставим метку в базе
    patient_id = await service.request_finish(message.from_user.id)
    
    if patient_id:
        await message.answer("⏳ Ожидаем подтверждения от пациента (5 минут)...")
        
        # Кнопки для пациента
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Завершить", callback_data="confirm_finish_yes")],
            [InlineKeyboardButton(text="❌ Продолжить", callback_data="confirm_finish_no")]
        ])
        
        try:
            await message.bot.send_message(
                patient_id, 
                "Доктор предлагает завершить консультацию. У вас остались вопросы?", 
                reply_markup=kb
            )
            
            # ЗАПУСКАЕМ ТАЙМЕР (в фоне)
            # Нам нужно узнать ID консультации для таймера. Найдем его через партнера.
            # (Тут небольшое упрощение: мы не передаем ID в таймер явно, а берем последний активный)
            # Но правильнее найти ID сейчас.
            # Для простоты сделаем проверку по ID врача внутри таймера.
            
            # Получаем ID текущей консультации для таймера
            # (в реальном проекте лучше передавать ID явно, но метод request_finish вернул только patient_id)
            # Допустим, мы запустим таймер, а он сам найдет ID внутри.
            
            # Трюк: чтобы не усложнять service, найдем consultation_id через 'get_active_partner' косвенно? 
            # Нет, давайте просто передадим ID врача в таймер, а там найдем.
            # (В коде ниже я использовал ID консультации, давайте получим его "честно").
            
            # Получаем ID консультации (немного костыль, но рабочий)
            # Мы знаем, что она активна.
            # Но для простоты: давайте в таймере искать по доктору.
            
            # А ладно, давайте проще:
            # Запустим задачу, передав ID юзера.
            pass
        except:
             await message.answer("Не удалось отправить запрос пациенту.")
             return

        # Запускаем таймер. Нам нужно получить ID консультации.
        # Я немного улучшу get_consultation_status в service? Нет, давайте сделаем хак.
        # Мы просто запустим таймер с ID юзера, а там разберемся.
        
        # ВАЖНО: asyncio.create_task требует текущий цикл событий.
        # Но чтобы передать ID консультации в wait_and_finish, нужно его знать.
        # Давайте просто перепишем wait_and_finish чуть ниже, чтобы он принимал doctor_id.
        
        asyncio.create_task(wait_and_finish_by_doctor(message.from_user.id, message.bot))

    else:
        await message.answer("У вас нет активной консультации или вы не врач.")

async def wait_and_finish_by_doctor(doctor_id: int, bot: Bot):
    await asyncio.sleep(300) # 5 минут
    async with async_session() as session:
        service = ConsultationService(session)
        # Ищем активную консультацию этого врача
        # (код дублируется, но это безопасно)
        from sqlalchemy import select, and_
        from database.models import Consultation
        
        query = select(Consultation).where(and_(Consultation.doctor_id == doctor_id, Consultation.status == "active"))
        result = await session.execute(query)
        cons = result.scalar_one_or_none()
        
        if cons and cons.finish_requested_at:
             await service.finish_consultation(doctor_id)
             try:
                await bot.send_message(cons.patient_id, "⏳ Автоматическое завершение (5 мин).")
                await bot.send_message(cons.doctor_id, "✅ Авто-завершение по таймеру.")
             except:
                pass


@router.callback_query(F.data == "confirm_finish_yes")
async def patient_confirmed(callback: CallbackQuery, service: ConsultationService):
    """Пациент нажал ДА"""
    partner_id = await service.finish_consultation(callback.from_user.id)
    if partner_id:
        await callback.message.edit_text("✅ Консультация завершена вами.")
        await callback.bot.send_message(partner_id, "✅ Пациент подтвердил завершение.")

@router.callback_query(F.data == "confirm_finish_no")
async def patient_declined(callback: CallbackQuery, service: ConsultationService):
    """Пациент нажал НЕТ"""
    await service.cancel_finish_request(callback.from_user.id)
    await callback.message.edit_text("Продолжаем консультацию.")
    
    partner_id = await service.get_active_partner(callback.from_user.id)
    if partner_id:
        await callback.bot.send_message(partner_id, "❌ Пациент отказался завершать. Продолжаем.")

@router.message()
async def forward_message(message: Message, service: ConsultationService):
    """Обычная пересылка + сброс таймера"""
    if message.text and message.text.startswith("/"): return

    partner_id = await service.get_active_partner(message.from_user.id)

    if partner_id:
        # !!! ВАЖНОЕ ИЗМЕНЕНИЕ !!!
        # Если пишет ЛЮБОЙ участник, мы сбрасываем "запрос завершения".
        # Потому что если пациент пишет вопрос - значит он не готов заканчивать.
        await service.cancel_finish_request(message.from_user.id)
        
        try:
            await message.send_copy(chat_id=partner_id)
        except:
            await message.answer("⚠️ Ошибка отправки.")
    else:
        if message.text:
            await message.answer("⛔ Вы не в чате. /start или /queue.")