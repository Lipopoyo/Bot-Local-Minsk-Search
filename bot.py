import asyncio
from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from handlers.bot import router

async def main():
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    print("Local Minsk Search is running.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
