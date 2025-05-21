import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from handlers import register_all_handlers


async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Перезапустить бота"),
        BotCommand(command="/scheduler", description="Расписание докладов"),
        BotCommand(command="/ask", description="Задать вопрос спикеру"),
        BotCommand(command="/active", description="Текущий доклад")
    ]
    await bot.set_my_commands(commands)


async def main():
    load_dotenv()
    TG_TOKEN = os.getenv('TG_TOKEN')

    bot = Bot(token=TG_TOKEN)
    dp = Dispatcher()

    logging.basicConfig(level=logging.INFO)

    await set_bot_commands(bot)

    register_all_handlers(dp)

    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())