import os
import asyncio
import logging

import aiogram
from aiogram.filters import CommandStart, Command
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.fsm.storage.redis import RedisStorage

from dotenv import load_dotenv
from app.handlers import router






async def main():
    load_dotenv()
    dp = Dispatcher()
    bot = Bot(token=os.getenv('BOT_TOKEN'))
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')