from aiogram import types, Dispatcher
from aiogram.filters import Command
from aiogram.enums import ParseMode
from datacenter.db_manager import get_all_talks
import asyncio
import logging


def escape_markdown(text: str) -> str:
    special_chars = r'_*[]()~`>#+-=|{}.!'
    return "".join(['\\' + char if char in special_chars else char for char in text])


def get_formatted_schedule() -> str:
    try:
        talks = get_all_talks()
    except Exception as e:
        logging.error(f"Ошибка при получении данных из БД: {e}")
        return "Не удалось загрузить расписание. Попробуйте позже."

    if not talks:
        return "🗓️ Расписание пока не составлено."

    schedule = ["🗓️ *Расписание Митапа:*\n\n"]

    for talk in talks:
        start_time = talk.start_time.strftime("%H:%M")
        end_time = talk.end_time.strftime("%H:%M")
        title = escape_markdown(talk.title)
        speaker = escape_markdown(talk.speaker.name)

        schedule.append(f"🕒 {start_time} \\- {end_time}: *{title}*")
        schedule.append(f"🗣️ Спикер: _{speaker}_\n")

    return "\n".join(schedule)


async def send_schedule(message: types.Message):
    loop = asyncio.get_event_loop()
    try:
        schedule_text = await loop.run_in_executor(None, get_formatted_schedule)
        await message.answer(schedule_text, parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        logging.error(f"Ошибка отправки расписания: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")


def register_scheduler_handlers(dp: Dispatcher):
    dp.message.register(send_schedule, Command("scheduler"))