import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from bot.handlers import patient, doctor
from bot.middlewares.db import DbSessionMiddleware
from database.base import init_db, async_session
from bot.handlers import patient, doctor, chat
from bot.handlers import patient, doctor, chat, admin

# Загружаем токен (лучше через dotenv)
TOKEN = "8490900753:AAEgSroh-yyWD1jQpCGX2-pFTWsMGL7mXdw" 

async def main():
    logging.basicConfig(level=logging.INFO)
    
    # 1. Инициализация БД
    await init_db()
    
    # 2. Бот и диспетчер
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    
    # 3. Подключаем мидлвар (БД)
    dp.update.middleware(DbSessionMiddleware(async_session))
    
    # 4. Роутеры
    dp.include_router(admin.router)
    dp.include_router(patient.router)
    dp.include_router(doctor.router)
    dp.include_router(chat.router)
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())