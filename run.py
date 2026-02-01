import asyncio
import logging
import os
import sys
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from bot.middlewares.db import DbSessionMiddleware
from database.base import init_db, async_session
from bot.handlers import patient, doctor, chat, admin
# Импортируем нашу новую функцию
from bot.navigation import set_default_menu 

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

async def main():
    logging.basicConfig(level=logging.INFO)
    await init_db()
    
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.update.middleware(DbSessionMiddleware(async_session))
    
    dp.include_router(admin.router)
    dp.include_router(patient.router)
    dp.include_router(doctor.router)
    dp.include_router(chat.router)
    
    # Ставим меню "по умолчанию" (только /start) для всех новичков
    await set_default_menu(bot)
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")