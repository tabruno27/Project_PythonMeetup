import os
from aiogram import types, Dispatcher
from aiogram.filters import Command
from dotenv import load_dotenv
from datacenter.db_manager import get_speaker_by_telegram_id, get_talks_by_speaker, get_questions_for_talk

load_dotenv()
ORGANIZER_TELEGRAM_ID = int(os.getenv('ORGANIZER_TELEGRAM_ID'))


async def handle_my_questions(message: types.Message):
    user_id = message.from_user.id

    speaker = get_speaker_by_telegram_id(user_id)

    if not speaker:
        await message.answer("❌ Только зарегистрированные спикеры могут просматривать вопросы к своим докладам.")
        return

    talks = get_talks_by_speaker(speaker.id)

    if not talks:
        await message.answer(f"👋 {speaker.name}, у вас нет запланированных докладов.")
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
        await message.answer(f"👋 {speaker.name}, пока нет вопросов к вашим докладам.")
        return

    await message.answer("\n".join(result_message))


def register_my_questions_handlers(dp: Dispatcher):
    dp.message.register(handle_my_questions, Command("my_questions"))