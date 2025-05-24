from aiogram import types, Dispatcher
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import os
from datacenter.db_manager import get_speaker_by_telegram_id
from commands import set_bot_commands

async def handle_start(message: types.Message):
    user_id = message.from_user.id

    keyboard = ReplyKeyboardBuilder()
    keyboard.add(types.KeyboardButton(text="/scheduler"))
    keyboard.add(types.KeyboardButton(text="/ask"))
    keyboard.add(types.KeyboardButton(text="/active"))

    if user_id == int(os.getenv('ORGANIZER_TELEGRAM_ID', '0')):
        keyboard.add(types.KeyboardButton(text="/add_speaker"))
        keyboard.add(types.KeyboardButton(text="/delete_speaker"))
        keyboard.add(types.KeyboardButton(text="/update_schedule"))
        role = "организатор"
    elif get_speaker_by_telegram_id(user_id):
        keyboard.add(types.KeyboardButton(text="/my_questions"))
        keyboard.add(types.KeyboardButton(text="/start_talk"))
        keyboard.add(types.KeyboardButton(text="/end_talk"))
        role = "спикер"
    else:
        role = "участник"

    try:
        await set_bot_commands(message.bot, user_id)
    except Exception as e:
        print(f"Ошибка при установке команд: {e}")
    
    welcome_text = (
        f"👋 Привет! Я бот для митапов. Вы вошли как: {role}\n\n"
        f"ℹ️ Доступные команды будут показаны в меню команд Telegram.\n\n"
        f"Просто нажми на нужную команду в меню или введи её вручную."
    )
    
    await message.answer(
        welcome_text,
        reply_markup=keyboard.as_markup(resize_keyboard=True)
    )

def register_start_handlers(dp: Dispatcher):
    dp.message.register(handle_start, Command("start"))