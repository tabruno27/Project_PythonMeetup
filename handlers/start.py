from aiogram import types, Dispatcher
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

async def handle_start(message: types.Message):
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(types.KeyboardButton(text="/scheduler"))
    keyboard.add(types.KeyboardButton(text="/ask"))
    keyboard.add(types.KeyboardButton(text="/active"))
    
    welcome_text = (
        "👋 Привет! Я бот для митапов. Выбери действие:\n\n"
        "ℹ️ Доступные команды:\n"
        "• /start - Перезапустить бота\n"
        "• /scheduler - Расписание докладов\n"
        "• /ask [вопрос] - Задать вопрос спикеру\n"
        "• /active - Текущий доклад\n\n"
        "Просто нажми на нужную команду в меню или введи её вручную."
    )
    
    await message.answer(
        welcome_text,
        reply_markup=keyboard.as_markup(resize_keyboard=True)
    )

def register_start_handlers(dp: Dispatcher):
    dp.message.register(handle_start, Command("start"))