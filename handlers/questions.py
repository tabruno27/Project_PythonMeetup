from aiogram import types, Dispatcher
from aiogram.filters import Command
from datacenter.db_manager import create_question, get_talk_by_id
from .talk_control import is_talk_active, get_active_talk_id
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import logging

logger = logging.getLogger(__name__)


async def handle_question(message: types.Message):
    try:
        # Создаем клавиатуру с командами
        keyboard = ReplyKeyboardBuilder()
        keyboard.add(types.KeyboardButton(text="/scheduler"))
        keyboard.add(types.KeyboardButton(text="/ask"))
        keyboard.add(types.KeyboardButton(text="/active"))
        
        if not is_talk_active():
            await message.answer("❌ Сейчас нет активного доклада для вопросов. Дождитесь начала выступления.",
                                 reply_markup=keyboard.as_markup(resize_keyboard=True))
            return

        active_talk_id = get_active_talk_id()
        talk = get_talk_by_id(active_talk_id)

        if not talk:
            await message.answer("❌ Не удалось получить информацию об активном докладе.",
                                 reply_markup=keyboard.as_markup(resize_keyboard=True))
            return

        command_parts = message.text.split(maxsplit=1)
        if len(command_parts) < 2:
            await message.answer(
                "📝 Пожалуйста, напишите вопрос после команды /ask\nПример: /ask Будет ли запись доклада?",
                reply_markup=keyboard.as_markup(resize_keyboard=True))
            return

        question_text = command_parts[1].strip()

        if not question_text:
            await message.answer(
                "📝 Пожалуйста, напишите вопрос после команды /ask\nПример: /ask Будет ли запись доклада?",
                reply_markup=keyboard.as_markup(resize_keyboard=True))
            return

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
            await message.answer(response, parse_mode="Markdown", reply_markup=keyboard.as_markup(resize_keyboard=True))
        else:
            await message.answer("❌ Не удалось сохранить вопрос. Попробуйте позже.",
                               reply_markup=keyboard.as_markup(resize_keyboard=True))

    except Exception as e:
        logger.error(f"Ошибка при обработке вопроса: {e}", exc_info=True)
        await message.answer("⚠️ Произошла ошибка при обработке вопроса. Попробуйте еще раз.")


async def handle_ask_command(message: types.Message):
    # Создаем клавиатуру с командами
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(types.KeyboardButton(text="/scheduler"))
    keyboard.add(types.KeyboardButton(text="/ask"))
    keyboard.add(types.KeyboardButton(text="/active"))
    
    if not is_talk_active():
        await message.answer(
            "❌ В данный момент нет активного доклада.\n"
            "Вопросы можно задавать только во время выступлений.",
            reply_markup=keyboard.as_markup(resize_keyboard=True)
        )
        return

    active_talk_id = get_active_talk_id()
    talk = get_talk_by_id(active_talk_id)

    help_text = (
        "📝 Чтобы задать вопрос спикеру, напишите команду в формате:\n"
        "`/ask Ваш вопрос здесь`\n\n"
        "*Пример:*\n"
        "/ask Будет ли доступна презентация после доклада?"
    )

    await message.answer(
        help_text,
        parse_mode="Markdown",
        reply_markup=keyboard.as_markup(resize_keyboard=True)
    )


def register_question_handlers(dp: Dispatcher):
    dp.message.register(handle_question, Command("ask"))
