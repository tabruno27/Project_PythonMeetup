import os
from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeChat
from datacenter.db_manager import get_speaker_by_telegram_id


# Определение роли пользователя
async def get_user_role(user_id: int) -> str:
    if user_id == int(os.getenv('ORGANIZER_TELEGRAM_ID', '0')):
        return 'organizer'
    
    speaker = get_speaker_by_telegram_id(user_id)
    if speaker:
        return 'speaker'
    
    return 'user'


async def set_bot_commands(bot: Bot, user_id: int = None):
    user_commands = [
        BotCommand(command="/start", description="Перезапустить бота"),
        BotCommand(command="/scheduler", description="Расписание докладов"),
        BotCommand(command="/ask", description="Задать вопрос спикеру"),
        BotCommand(command="/active", description="Текущий доклад"),
    ]
    
    # Дополнительные команды для спикеров
    speaker_commands = user_commands + [
        BotCommand(command="/my_questions", description="Вопросы к моим докладам"),
        BotCommand(command="/start_talk", description="Начать доклад"),
        BotCommand(command="/end_talk", description="Завершить доклад"),
    ]
    
    # Команды для организаторов
    organizer_commands = user_commands + [
        BotCommand(command="/add_speaker", description="Добавить спикера"),
        BotCommand(command="/delete_speaker", description="Удалить спикера"),
        BotCommand(command="/update_schedule", description="Обновить расписание"),
    ]

    if user_id:
        role = await get_user_role(user_id)
        if role == 'organizer':
            await bot.set_my_commands(organizer_commands, scope=BotCommandScopeChat(chat_id=user_id))
        elif role == 'speaker':
            await bot.set_my_commands(speaker_commands, scope=BotCommandScopeChat(chat_id=user_id))
        else:
            await bot.set_my_commands(user_commands, scope=BotCommandScopeChat(chat_id=user_id))
    else:
        await bot.set_my_commands(user_commands)
