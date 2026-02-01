from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault

# 1. Список для ОБЫЧНЫХ пользователей (и гостей)
USER_COMMANDS = [
    BotCommand(command="start", description="🚀 Главное меню"),
]

# 2. Список для ВРАЧЕЙ
DOCTOR_COMMANDS = [
    BotCommand(command="start", description="🔄 Перезагрузка"),
    BotCommand(command="queue", description="👨‍⚕️ Взять пациента"),
    BotCommand(command="finish", description="✅ Завершить чат"),
]

# 3. Список для АДМИНОВ
ADMIN_COMMANDS = [
    BotCommand(command="start", description="🔄 Перезагрузка"),
    BotCommand(command="check_user", description="🔍 Проверить"),
    BotCommand(command="promote", description="⬆️ Назначить врача"),
    BotCommand(command="demote", description="⬇️ Разжаловать"),
    BotCommand(command="admin_help", description="ℹ️ Помощь"),
]

async def set_user_menu(bot: Bot, chat_id: int, role: str):
    """
    Устанавливает личное меню для конкретного пользователя
    в зависимости от его роли.
    """
    if role == "admin":
        commands = ADMIN_COMMANDS
    elif role == "doctor":
        commands = DOCTOR_COMMANDS
    else:
        commands = USER_COMMANDS
        
    # Магия: scope=BotCommandScopeChat(chat_id=...) меняет меню только ОДНОМУ человеку
    await bot.set_my_commands(commands, scope=BotCommandScopeChat(chat_id=chat_id))

async def set_default_menu(bot: Bot):
    """Меню по умолчанию (для тех, кто только зашел)"""
    await bot.set_my_commands(USER_COMMANDS, scope=BotCommandScopeDefault())