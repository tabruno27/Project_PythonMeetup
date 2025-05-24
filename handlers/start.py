from aiogram import types, Dispatcher
from aiogram.filters import Command
import os
from datacenter.db_manager import get_speaker_by_telegram_id
from commands import set_bot_commands, get_user_role, get_keyboard_for_role

async def handle_start(message: types.Message):
    user_id = message.from_user.id
    
    # Определяем роль пользователя для отображения в сообщении
    role_name = "участник"
    role = await get_user_role(user_id)
    
    if role == "organizer":
        role_name = "организатор"
    elif role == "speaker":
        role_name = "спикер"
    
    # Получаем клавиатуру в соответствии с ролью
    keyboard = get_keyboard_for_role(role)
    
    try:
        # Обновляем команды в меню
        await set_bot_commands(message.bot, user_id)
    except Exception as e:
        print(f"Ошибка при установке команд: {e}")
    
    welcome_text = (
        f"👋 Привет! Я бот для митапов. Вы вошли как: {role_name}\n\n"
        f"ℹ️ Доступные команды будут показаны в меню команд Telegram.\n\n"
        f"Просто нажми на нужную команду в меню или введи её вручную."
    )
    
    await message.answer(
        welcome_text,
        reply_markup=keyboard.as_markup(resize_keyboard=True)
    )

def register_start_handlers(dp: Dispatcher):
    dp.message.register(handle_start, Command("start"))