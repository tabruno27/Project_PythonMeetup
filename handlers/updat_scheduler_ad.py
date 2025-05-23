import os
from aiogram import types, Dispatcher
from aiogram.filters import Command
from dotenv import load_dotenv
from datacenter.db_manager import (update_talk, get_talks_by_speaker,
                                   get_speaker_by_id, get_all_participants, get_talk_by_id)
from aiogram import Bot
import datetime


load_dotenv()
ORGANIZER_TELEGRAM_ID = int(os.getenv('ORGANIZER_TELEGRAM_ID'))

# Хранение временных данных для обновления расписания
pending_update_data = {}

async def cmd_update_schedule(message: types.Message):
    if message.from_user.id != ORGANIZER_TELEGRAM_ID:
        await message.answer("Извините, у вас нет прав для выполнения этой команды.")
        return

    await message.answer("Введите ID спикера, чью программу вы хотите обновить:")
    pending_update_data[message.from_user.id] = {"step": "waiting_for_speaker_id"}

async def process_update_schedule(message: types.Message):
    user_id = message.from_user.id

    if user_id in pending_update_data:
        step = pending_update_data[user_id]["step"]

        if step == "waiting_for_speaker_id":
            speaker_id_str = message.text.strip()

            if not speaker_id_str.isdigit():
                await message.answer("ID должен содержать только цифры. Попробуйте еще раз:")
                return

            speaker_id = int(speaker_id_str)
            speaker = get_speaker_by_id(speaker_id)

            if not speaker:
                await message.answer(f"Спикер с ID {speaker_id} не найден. Попробуйте еще раз:")
                return

            # Получаем расписание спикера
            talks = get_talks_by_speaker(speaker_id)
            if not talks:
                await message.answer(f"У спикера {speaker.name} нет запланированных докладов.")
                del pending_update_data[user_id]
                return

            # Отправляем расписание спикера
            schedule_message = "\n".join([f"{talk.id}: '{talk.title}' с {talk.start_time} до {talk.end_time}" for talk in talks])
            await message.answer(f"Расписание спикера {speaker.name}:\n{schedule_message}\nВведите ID доклада, который хотите обновить:")
            pending_update_data[user_id]["step"] = "waiting_for_talk_id"
            pending_update_data[user_id]["speaker_id"] = speaker_id

        elif step == "waiting_for_talk_id":
            talk_id_str = message.text.strip()

            if not talk_id_str.isdigit():
                await message.answer("ID должен содержать только цифры. Попробуйте еще раз:")
                return

            talk_id = int(talk_id_str)
            talk = get_talk_by_id(talk_id)

            if not talk or talk.speaker.id != pending_update_data[user_id]["speaker_id"]:
                await message.answer("Доклад с таким ID не найден или он не принадлежит этому спикеру. Попробуйте еще раз:")
                return

            # Запрашиваем новые данные для доклада
            await message.answer("Введите новое название доклада:")
            pending_update_data[user_id]["talk_id"] = talk_id
            pending_update_data[user_id]["step"] = "waiting_for_title"

        elif step == "waiting_for_title":
            new_title = message.text.strip()
            talk_id = pending_update_data[user_id]["talk_id"]

            await message.answer("Введите новое время начала (в формате YYYY-MM-DD HH:MM):")
            pending_update_data[user_id]["new_title"] = new_title
            pending_update_data[user_id]["step"] = "waiting_for_start_time"

        elif step == "waiting_for_start_time":
            new_start_time_str = message.text.strip()
            try:
                new_start_time = datetime.datetime.strptime(new_start_time_str, "%Y-%m-%d %H:%M")
            except ValueError:
                await message.answer("Неверный формат времени. Попробуйте еще раз:")
                return

            await message.answer("Введите новое время окончания (в формате YYYY-MM-DD HH:MM):")
            pending_update_data[user_id]["new_start_time"] = new_start_time
            pending_update_data[user_id]["step"] = "waiting_for_end_time"

        elif step == "waiting_for_end_time":
            new_end_time_str = message.text.strip()
            try:
                new_end_time = datetime.datetime.strptime(new_end_time_str, "%Y-%m-%d %H:%M")
            except ValueError:
                await message.answer("Неверный формат времени. Попробуйте еще раз:")
                return

                # Получаем новые данные
            talk_id = pending_update_data[user_id]["talk_id"]
            new_title = pending_update_data[user_id]["new_title"]
            new_start_time = pending_update_data[user_id]["new_start_time"]
            new_end_time = new_end_time

            # Обновляем доклад в базе данных
            updated_talk = update_talk(talk_id, new_title=new_title, new_start_time=new_start_time,
                                       new_end_time=new_end_time)

            if updated_talk:
                await message.answer("Программа успешно обновлена.")

                # Уведомляем всех участников о том, что программа обновлена
                await notify_participants(updated_talk)

            else:
                await message.answer("Произошла ошибка при обновлении программы. Попробуйте еще раз.")

            # Удаляем временные данные после завершения процесса
            del pending_update_data[user_id]


async def notify_participants(message: types.Message, speaker_id: int, title: str, start_time: datetime.datetime, end_time: datetime.datetime):
    participants = get_all_participants()  # Функция получения всех участников

    start_time_str = start_time.strftime('%Y-%m-%d %H:%M')
    end_time_str = end_time.strftime('%Y-%m-%d %H:%M')

    for participant in participants:

        message_text = (
            f"📢 Программа обновлена!\n\n"
            f"🗣 Доклад: {title}\n"
            f"🕒 Время: {start_time_str} - {end_time_str}\n"
            f"🔗 Спикер ID: {speaker_id}\n"
            f"Не пропустите!"
        )
        await message.bot.send_message(chat_id=participant["telegram_id"], text=message_text)



def register_up_sheduler_handlers(dp: Dispatcher):
    dp.message.register(cmd_update_schedule, Command("update_schedule"))
    dp.message.register(process_update_schedule)
