from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from core.services import ConsultationService
from bot.filters import IsAdmin
from bot.navigation import set_user_menu

router = Router()
router.message.filter(IsAdmin())

class AdminStates(StatesGroup):
    waiting_for_promote_user = State()
    waiting_for_demote_user = State()
    waiting_for_check_user = State()

# --- CHECK USER ---
@router.message(Command("check_user"))
async def check_user_start(message: Message, command: CommandObject, state: FSMContext, service: ConsultationService):
    if command.args:
        await perform_check_user(message, command.args, service)
        return
    await message.answer("Введите username или ID для проверки:")
    await state.set_state(AdminStates.waiting_for_check_user)

@router.message(AdminStates.waiting_for_check_user)
async def check_user_finish(message: Message, state: FSMContext, service: ConsultationService):
    await perform_check_user(message, message.text, service)
    await state.clear()

async def perform_check_user(message: Message, arg: str, service: ConsultationService):
    arg = arg.strip()
    
    # ЛОГИКА УЛУЧШЕНА:
    if arg.isdigit():
        # Если только цифры - ищем по ID
        role = await service.get_user_role(int(arg))
        await message.answer(f"🆔 ID: {arg}\nRole: {role}")
    else:
        # Во всех остальных случаях считаем, что это никнейм (даже без @)
        user = await service.get_user_by_username(arg)
        if user:
            await message.answer(f"👤 Пользователь: @{user.username}\n🆔 ID: {user.telegram_id}\nRole: {user.role}")
        else:
            await message.answer(f"❌ Пользователь '{arg}' не найден в базе.")

# --- PROMOTE ---
@router.message(Command("promote"))
async def promote_start(message: Message, command: CommandObject, state: FSMContext, service: ConsultationService):
    if command.args:
        await perform_promote(message, command.args, service)
        return
    await message.answer("Введите username или ID нового врача:")
    await state.set_state(AdminStates.waiting_for_promote_user)

@router.message(AdminStates.waiting_for_promote_user)
async def promote_finish(message: Message, state: FSMContext, service: ConsultationService):
    await perform_promote(message, message.text, service)
    await state.clear()

async def perform_promote(message: Message, arg: str, service: ConsultationService):
    arg = arg.strip()
    target_id = None
    
    if arg.isdigit():
        target_id = int(arg)
    else:
        # Ищем по нику (автоматически добавит или уберет @ внутри сервиса)
        user = await service.get_user_by_username(arg)
        if user:
            target_id = user.telegram_id
        else:
            await message.answer("❌ Пользователь не найден. Убедитесь, что он нажал /start")
            return
    
    if target_id:
        
        await service.set_user_role(target_id, "doctor")
        await message.answer(f"✅ Пользователь {arg} назначен ВРАЧОМ.")
        try:
            await set_user_menu(message.bot, target_id, "doctor")
            await message.bot.send_message(target_id, "🎉 Вам выданы права ВРАЧА. Нажмите /queue для работы.")
        except:
            pass

# --- DEMOTE ---
@router.message(Command("demote"))
async def demote_start(message: Message, command: CommandObject, state: FSMContext, service: ConsultationService):
    if command.args:
        await perform_demote(message, command.args, service)
        return
    await message.answer("Введите username или ID для разжалования:")
    await state.set_state(AdminStates.waiting_for_demote_user)

@router.message(AdminStates.waiting_for_demote_user)
async def demote_finish(message: Message, state: FSMContext, service: ConsultationService):
    await perform_demote(message, message.text, service)
    await state.clear()

async def perform_demote(message: Message, arg: str, service: ConsultationService):
    arg = arg.strip()
    target_id = None
    
    if arg.isdigit():
        target_id = int(arg)
    else:
        user = await service.get_user_by_username(arg)
        if user:
            target_id = user.telegram_id
        else:
            await message.answer("❌ Пользователь не найден.")
            return

    if target_id:
        await service.set_user_role(target_id, "patient")
        await message.answer(f"✅ Пользователь {arg} разжалован.")
        try:
            await set_user_menu(message.bot, target_id, "patient")
            await message.bot.send_message(target_id, "⚠️ Ваши права врача отозваны.")
        except:
            pass

@router.message(Command("admin_help"))
async def admin_help(message: Message):
    await message.answer("Админка:\n/promote, /demote, /check_user")