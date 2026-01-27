from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from core.services import ConsultationService
from bot.filters import IsAdmin

router = Router()

# Все команды в этом роутере доступны только Админу
router.message.filter(IsAdmin())

@router.message(Command("admin_help"))
async def admin_help(message: Message):
    text = (
        "👑 **Панель Администратора**\n\n"
        "/promote <ID> - Назначить пользователя Врачом\n"
        "/demote <ID> - Разжаловать в Пациенты\n"
        "/check_user <ID> - Узнать роль пользователя"
    )
    await message.answer(text, parse_mode="Markdown")

@router.message(Command("promote"))
async def promote_user(message: Message, command: CommandObject, service: ConsultationService):
    """Назначить врача: /promote 123456789"""
    if not command.args:
        await message.answer("⚠️ Укажите ID пользователя.\nПример: `/promote 123456789`")
        return

    try:
        user_id = int(command.args)
        # Назначаем роль 'doctor'
        await service.set_user_role(user_id, "doctor")
        await message.answer(f"✅ Пользователь `{user_id}` назначен ВРАЧОМ.", parse_mode="Markdown")
        
        # Опционально: можно попробовать отправить уведомление новому врачу
        try:
            await message.bot.send_message(user_id, "🎉 Вам выданы права ВРАЧА. Нажмите /queue для работы.")
        except:
            await message.answer("⚠️ Права выданы, но я не смог уведомить пользователя (он не запускал бота).")
            
    except ValueError:
        await message.answer("❌ ID должен быть числом.")

@router.message(Command("demote"))
async def demote_user(message: Message, command: CommandObject, service: ConsultationService):
    """Уволить врача: /demote 123456789"""
    if not command.args:
        await message.answer("⚠️ Укажите ID.")
        return

    try:
        user_id = int(command.args)
        await service.set_user_role(user_id, "patient")
        await message.answer(f"✅ Пользователь `{user_id}` разжалован в пациенты.", parse_mode="Markdown")
    except ValueError:
        await message.answer("❌ Некорректный ID.")