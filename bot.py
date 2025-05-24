import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from handlers import register_all_handlers
from datacenter.db_manager import create_tables


async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Перезапустить бота"),
        BotCommand(command="/scheduler", description="Расписание докладов"),
        BotCommand(command="/ask", description="Задать вопрос спикеру"),
        BotCommand(command="/active", description="Текущий доклад"),
        BotCommand(command="/add_speaker", description="Добавить спикера"),
        BotCommand(command="/delete_speaker", description="Удалить спикера"),
        BotCommand(command="/update_schedule", description="Обновить расписание")
    ]
    await bot.set_my_commands(commands)


async def main():
    load_dotenv()
    tg_token = os.getenv('TG_TOKEN')

    if not tg_token:
        logging.error("Ошибка: Токен бота не найден в переменных окружения")
        return

    create_tables()

    bot = Bot(token=tg_token)
    dp = Dispatcher()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logging.info("Запуск бота...")

    await set_bot_commands(bot)
    register_all_handlers(dp)

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())
