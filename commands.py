import os
from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeChat, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from datacenter.db_manager import get_speaker_by_telegram_id


# Определение роли пользователя
async def get_user_role(user_id: int) -> str:
    if user_id == int(os.getenv('ORGANIZER_TELEGRAM_ID', '0')):
        return 'organizer'
    
    speaker = get_speaker_by_telegram_id(user_id)
    if speaker:
        return 'speaker'
    
    return 'user'


def get_keyboard_for_role(role: str) -> ReplyKeyboardBuilder:
    """
    Создает клавиатуру в зависимости от роли пользователя
    
    Args:
        role: Роль пользователя ('user', 'speaker', 'organizer')
        
    Returns:
        ReplyKeyboardBuilder: Объект клавиатуры с кнопками
    """
    kb = ReplyKeyboardBuilder()
    
    # Базовые кнопки для всех пользователей
    kb.add(
        KeyboardButton(text="/scheduler"),
        KeyboardButton(text="/active"),
        KeyboardButton(text="/ask")
    )
    
    # Дополнительные кнопки для спикеров
    if role == 'speaker':
        kb.row(
            KeyboardButton(text="/my_questions"),
            KeyboardButton(text="/start_talk"),
            KeyboardButton(text="/end_talk")
        )
    
    # Дополнительные кнопки для организаторов
    elif role == 'organizer':
        kb.row(
            KeyboardButton(text="/add_speaker"),
            KeyboardButton(text="/delete_speaker")
        )
        kb.row(
            KeyboardButton(text="/update_schedule")
        )
    
    # Настраиваем размер клавиатуры (2 кнопки в ряду)
    if role == 'user':
        kb.adjust(2)
    else:
        kb.adjust(3, 2)
    
    return kb


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
