import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from datacenter.db_manager import create_tables
from commands import set_bot_commands
from handlers import register_all_handlers


# Обработчик для обновления команд при каждом сообщении
async def update_commands_handler(message: types.Message):
    user_id = message.from_user.id
    try:
        # Обновляем команды бота в меню
        await set_bot_commands(message.bot, user_id)
        
        # Не отправляем клавиатуру при каждом сообщении, чтобы не мешать пользователю
        # Клавиатура будет обновляться только при выполнении команд
    except Exception as e:
        logging.debug(f"Ошибка при обновлении команд для пользователя {user_id}: {e}")


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

    # Устанавливаем базовые команды для всех пользователей
    await set_bot_commands(bot)
    register_all_handlers(dp)
    
    # Регистрируем обработчик для обновления команд
    dp.message.register(update_commands_handler)

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())
