from aiogram import types, Dispatcher
from aiogram.filters import Command
from datacenter.db_manager import get_current_talk, create_question
import logging

logger = logging.getLogger(__name__)

async def handle_question(message: types.Message):
    """Обработчик команды /ask с текстом вопроса"""
    try:
        # Получаем текущий доклад
        talk = get_current_talk()
        if not talk:
            await message.answer("❌ Сейчас нет активного доклада для вопросов.", reply_markup=types.ReplyKeyboardRemove())
            return

        # Извлекаем текст вопроса
        question_text = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
        
        if not question_text:
            await message.answer("📝 Пожалуйста, напишите вопрос после команды /ask\nПример: /ask Будет ли запись доклада?")
            return

        # Создаем вопрос в БД
        question = create_question(
            talk_id=talk.id,
            guest_telegram_id=message.from_user.id,
            text=question_text
        )

        if question:
            response = (
                "✅ Ваш вопрос успешно отправлен!\n\n"
                f"*Доклад:* {talk.title}\n"
                f"*Спикер:* {talk.speaker.name}\n"
                "Спасибо за активное участие!"
            )
            await message.answer(response, parse_mode="Markdown", reply_markup=types.ReplyKeyboardRemove())
        else:
            await message.answer("❌ Не удалось сохранить вопрос. Попробуйте позже.")

    except Exception as e:
        logger.error(f"Error processing question: {e}", exc_info=True)
        await message.answer("⚠️ Произошла ошибка при обработке вопроса. Попробуйте еще раз.")

async def handle_ask_command(message: types.Message):
    """Обработчик команды /ask без текста"""
    talk = get_current_talk()
    if not talk:
        await message.answer(
            "❌ В данный момент нет активного доклада.\n"
            "Вопросы можно задавать только во время выступлений.",
            reply_markup=types.ReplyKeyboardRemove()
        )
        return
        
    help_text = (
        "📝 Чтобы задать вопрос спикеру, напишите команду в формате:\n"
        "`/ask Ваш вопрос здесь`\n\n"
        "*Пример:*\n"
        "/ask Будет ли доступна презентация после доклада?"
    )
    
    await message.answer(
        help_text,
        parse_mode="Markdown",
        reply_markup=types.ReplyKeyboardRemove()
    )

def register_question_handlers(dp: Dispatcher):
    dp.message.register(handle_ask_command, Command("ask"))
    dp.message.register(handle_question, Command("ask"))