import asyncio
import asyncpg
import sys

# ВАШИ ДАННЫЕ ИЗ .ENV
DB_USER = "postgres"
DB_PASS = "K17062006k"  # Ваш пароль из скрина
DB_HOST = "127.0.0.1"
DB_NAME = "doctor_bot"

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def test():
    print(f"🔌 Пробую подключиться к {DB_HOST}...")
    try:
        conn = await asyncpg.connect(user=DB_USER, password=DB_PASS, database=DB_NAME, host=DB_HOST)
        print("✅ УСПЕХ! Пароль верный, база доступна.")
        await conn.close()
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")

asyncio.run(test())