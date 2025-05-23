import os
from aiogram import types, Dispatcher
from aiogram.filters import Command
from dotenv import load_dotenv
from datacenter.db_manager import (create_speaker, get_speaker_by_telegram_id, create_talk)
from aiogram import Bot  # Импортируйте объект бота, если он доступен
import datetime


load_dotenv()
ORGANIZER_TELEGRAM_ID = int(os.getenv('ORGANIZER_TELEGRAM_ID'))

# Хранение временных данных
pending_speaker_data = {}


async def cmd_add_speaker(message: types.Message):
    if message.from_user.id != ORGANIZER_TELEGRAM_ID:
        await message.answer("Извините, у вас нет прав для выполнения этой команды.")
        return

    await message.answer("Введите Telegram ID спикера (только цифры):")

    # Сохраняем ID организатора для дальнейшего использования
    pending_speaker_data[message.from_user.id] = {"step": "waiting_for_speaker_id"}


async def process_message_add(message: types.Message):
    user_id = message.from_user.id

    if user_id in pending_speaker_data:
        step = pending_speaker_data[user_id]["step"]

        if step == "waiting_for_speaker_id":
            speaker_id_str = message.text.strip()
            if not speaker_id_str.isdigit():
                await message.answer("ID должен содержать только цифры. Попробуйте еще раз:")
                return

            speaker_id = int(speaker_id_str)
            existing_speaker = get_speaker_by_telegram_id(speaker_id)
            if existing_speaker:
                await message.answer(
                    f"Спикер с Telegram ID {speaker_id} уже существует в базе: {existing_speaker.name}")
                del pending_speaker_data[user_id]
                return

            pending_speaker_data[user_id]["speaker_id"] = speaker_id
            pending_speaker_data[user_id]["step"] = "waiting_for_speaker_name"
            await message.answer("Введите фамилию и имя спикера:")

        elif step == "waiting_for_speaker_name":
            speaker_name = message.text.strip()
            if not speaker_name:
                await message.answer("Имя не может быть пустым. Пожалуйста, введите фамилию и имя спикера:")
                return

            pending_speaker_data[user_id]["speaker_name"] = speaker_name
            pending_speaker_data[user_id]["step"] = "waiting_for_talk_title"
            await message.answer("Введите название доклада:")

        elif step == "waiting_for_talk_title":
            talk_title = message.text.strip()
            if not talk_title:
                await message.answer("Название доклада не может быть пустым. Пожалуйста, введите название доклада:")
                return

            pending_speaker_data[user_id]["talk_title"] = talk_title
            pending_speaker_data[user_id]["step"] = "waiting_for_start_time"
            await message.answer("Введите время начала доклада (например, 14:00):")

        elif step == "waiting_for_start_time":
            start_time_str = message.text.strip()
            try:
                start_time = datetime.datetime.strptime(start_time_str, "%H:%M")
            except ValueError:
                await message.answer("Неверный формат времени. Пожалуйста, введите время в формате ЧЧ:ММ (например, 14:00):")
                return

            pending_speaker_data[user_id]["start_time"] = start_time
            pending_speaker_data[user_id]["step"] = "waiting_for_end_time"
            await message.answer("Введите время окончания доклада (например, 15:00):")

        elif step == "waiting_for_end_time":
            end_time_str = message.text.strip()
            try:
                end_time = datetime.datetime.strptime(end_time_str, "%H:%M")
            except ValueError:
                await message.answer("Неверный формат времени. Пожалуйста, введите время в формате ЧЧ:ММ (например, 15:00):")
                return

            start_time = pending_speaker_data[user_id]["start_time"]
            if end_time <= start_time:
                await message.answer("Время окончания должно быть позже времени начала. Пожалуйста, введите корректное время окончания:")
                return

            pending_speaker_data[user_id]["end_time"] = end_time

            # Собираем все данные
            speaker_id = pending_speaker_data[user_id]["speaker_id"]
            speaker_name = pending_speaker_data[user_id]["speaker_name"]
            talk_title = pending_speaker_data[user_id]["talk_title"]
            start_time = pending_speaker_data[user_id]["start_time"]
            end_time = pending_speaker_data[user_id]["end_time"]

            # Сохраняем спикера в базе
            speaker = create_speaker(name=speaker_name, telegram_id=speaker_id)
            if not speaker:
                await message.answer("Произошла ошибка при добавлении спикера. Возможно, такой ID уже существует.")
                del pending_speaker_data[user_id]
                return

            # Создаем доклад
            talk = create_talk(
                speaker_id=speaker.id,
                title=talk_title,
                start_time=start_time,
                end_time=end_time
            )
            if not talk:
                await message.answer("Произошла ошибка при добавлении доклада.")
                del pending_speaker_data[user_id]
                return

            await message.answer(
                f"Спикер '{speaker_name}' с докладом '{talk_title}' успешно добавлен.\n"
                f"Время доклада: с {start_time.strftime('%H:%M')} по {end_time.strftime('%H:%M')}."
            )

            await message.bot.send_message(
                chat_id=speaker_id,
                text=(
                    f"Здравствуйте, {speaker_name}!\n"
                    f"Вас добавили в список спикеров на мероприятии.\n"
                    f"Ваш доклад: {talk_title}\n"
                    f"Время выступления: с {start_time.strftime('%H:%M')} по {end_time.strftime('%H:%M')}."
                )
            )

            del pending_speaker_data[user_id] # Удаляем данные после завершения процесса


def register_create_speaker_ad_handlers(dp: Dispatcher):
    dp.message.register(cmd_add_speaker, Command("add_speaker"))
    dp.message.register(process_message_add)



