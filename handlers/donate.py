from aiogram import types, Dispatcher
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram import F
from aiogram.types import URLInputFile
import logging

logger = logging.getLogger(__name__)

async def handle_donate(message: types.Message):
    try:
        donate_text = (
            "🎉 Поддержать проект можно по ссылке:\n"
            "https://pay.cloudtips.ru/p/2bc2ef7b\n\n"
            "Спасибо за вашу поддержку! ❤️"
        )
        
        await message.answer(
            donate_text,
            reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[[
                    types.InlineKeyboardButton(
                        text="💳 Перейти к оплате", 
                        url="https://pay.cloudtips.ru/p/2bc2ef7b"
                    )
                ]]
            )
        )
        
    except Exception as e:
        logger.error(f"Ошибка обработки доната: {e}")
        await message.answer("⚠️ Произошла ошибка при обработке запроса")

def register_donate_handlers(dp: Dispatcher):
    dp.message.register(handle_donate, F.text == "💎 Поддержать проект")
