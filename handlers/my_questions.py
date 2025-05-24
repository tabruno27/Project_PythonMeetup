import os
from aiogram import types, Dispatcher
from aiogram.filters import Command
from dotenv import load_dotenv
from datacenter.db_manager import get_speaker_by_telegram_id, get_talks_by_speaker, get_questions_for_talk
from commands import set_bot_commands, get_user_role, get_keyboard_for_role

load_dotenv()
ORGANIZER_TELEGRAM_ID = int(os.getenv('ORGANIZER_TELEGRAM_ID'))


async def handle_my_questions(message: types.Message):
    user_id = message.from_user.id

    speaker = get_speaker_by_telegram_id(user_id)

    # Получаем роль пользователя
    role = await get_user_role(user_id)
    
    # Получаем клавиатуру соответствующую роли пользователя
    keyboard = get_keyboard_for_role(role)

    if not speaker:
        await message.answer(
            "❌ Только зарегистрированные спикеры могут просматривать вопросы к своим докладам.",
            reply_markup=keyboard.as_markup(resize_keyboard=True)
        )
        # Обновляем команды для этого пользователя, если он пытается выполнить команду спикера
        try:
            await set_bot_commands(message.bot, user_id)
        except Exception as e:
            print(f"Ошибка при обновлении команд: {e}")
        return

    talks = get_talks_by_speaker(speaker.id)

    if not talks:
        await message.answer(
            f"👋 {speaker.name}, у вас нет запланированных докладов.",
            reply_markup=keyboard.as_markup(resize_keyboard=True)
        )
        return

    result_message = [f"📝 {speaker.name}, вот вопросы к вашим докладам:"]

    has_questions = False

    for talk in talks:
        questions = get_questions_for_talk(talk.id)

        if not questions:
            continue

        has_questions = True
        result_message.append(f"\n🗣 Доклад: {talk.title}")

        for i, question in enumerate(questions, 1):
            status = "✅" if question.answered else "❓"
            result_message.append(f"{i}. {status} {question.text}")

        result_message.append("")  # пустая строка для разделения

    if not has_questions:
        await message.answer(
            f"👋 {speaker.name}, пока нет вопросов к вашим докладам.",
            reply_markup=keyboard.as_markup(resize_keyboard=True)
        )
        return

    await message.answer(
        "\n".join(result_message),
        reply_markup=keyboard.as_markup(resize_keyboard=True)
    )


def register_my_questions_handlers(dp: Dispatcher):
    dp.message.register(handle_my_questions, Command("my_questions"))