import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from handlers import register_all_handlers


async def main():
    load_dotenv()
    TG_TOKEN = os.getenv('TG_TOKEN')

    bot = Bot(token=TG_TOKEN)
    dp = Dispatcher()

    logging.basicConfig(level=logging.INFO)

    register_all_handlers(dp)

    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())