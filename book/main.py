import asyncio

from aiogram import Bot, Dispatcher

from database.db import create_db
from handlers import basic, booking
from utils.config import TELEGRAM_API_TOKEN


async def main():
    create_db()

    dp = Dispatcher()
    bot = Bot(token=TELEGRAM_API_TOKEN)

    dp.include_router(basic.router)
    dp.include_router(booking.router)

    print('Бот запущен!')
    await dp.start_polling(bot)
    await bot.delete_webhook(drop_pending_updates=True)


if __name__ == '__main__':
    asyncio.run(main())
