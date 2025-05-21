from aiogram import types, Dispatcher
from aiogram.filters import Command
from datacenter.db_manager import get_current_talk

async def handle_active_command(message: types.Message):
    """Обработчик команды /active"""
    talk = get_current_talk()
    if not talk:
        await message.answer(
            "❌ В данный момент нет активного доклада.",
            reply_markup=types.ReplyKeyboardRemove()
        )
        return
        
    response = (
        "🎤 *Текущий доклад:*\n\n"
        f"*Название:* {talk.title}\n"
        f"*Спикер:* {talk.speaker.name}\n"
        f"*Время:* {talk.start_time.strftime('%H:%M')} - {talk.end_time.strftime('%H:%M')}"
    )
    
    await message.answer(
        response,
        parse_mode="Markdown",
        reply_markup=types.ReplyKeyboardRemove()
    )

def register_active_handlers(dp: Dispatcher):
    dp.message.register(handle_active_command, Command("active"))