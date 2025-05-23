import os
from aiogram import types, Dispatcher
from aiogram.filters import Command
from dotenv import load_dotenv
from datacenter.db_manager import (delete_speaker, get_speaker_by_id,
                                   delete_talk_by_speaker_id)


load_dotenv()
ORGANIZER_TELEGRAM_ID = int(os.getenv('ORGANIZER_TELEGRAM_ID'))

# Хранение временных данных
pending_speaker_data = {}


async def cmd_delete_speaker(message: types.Message):
    user_id = message.from_user.id

    # Проверяем, является ли пользователь организатором
    if user_id != ORGANIZER_TELEGRAM_ID:
        await message.answer("У вас нет прав на выполнение этой команды.")
        return

    # Запрашиваем ID спикера для удаления
    pending_speaker_data[user_id] = {"step": "waiting_for_speaker_id"}
    await message.answer("Введите ID спикера, которого необходимо удалить:")

async def process_message_del(message: types.Message):
    user_id = message.from_user.id

    if user_id in pending_speaker_data:
        step = pending_speaker_data[user_id]["step"]

        if step == "waiting_for_speaker_id":
            speaker_id_str = message.text.strip()
            # Проверяем, является ли ID числом
            if not speaker_id_str.isdigit():
                await message.answer("ID должен содержать только цифры. Попробуйте еще раз:")
                return

            # Преобразуем строку в целое число
            speaker_id = int(speaker_id_str)

            # Теперь вызываем функцию для удаления спикера
            success, response_message = await cmd_delete_speaker_by_id(speaker_id)

            await message.answer(response_message)
            del pending_speaker_data[user_id]  # Удаляем данные пользователя
        else:
            await message.answer("Пожалуйста, введите ID спикера для удаления.")
    else:
        await message.answer("Сначала используйте команду /delete_speaker для начала процесса удаления.")

async def cmd_delete_speaker_by_id(speaker_id):
    # Получаем информацию о спикере
    speaker = get_speaker_by_id(speaker_id)
    if not speaker:
        return False, "Спикер не найден."

    # Удаляем все доклады спикера (если они есть)
    talks_deleted = delete_talk_by_speaker_id(speaker_id)

    # Удаляем спикера
    speaker_deleted = delete_speaker(speaker_id)

    if speaker_deleted:
        if talks_deleted:
            return True, f"Спикер '{speaker.name}' и его доклад(ы) успешно удалены."
        else:
            return True, f"Спикер '{speaker.name}' успешно удален. У него не было докладов."
    else:
        return False, "Произошла ошибка при удалении спикера."


def register_delete_speaker_ad_handlers(dp: Dispatcher):
    dp.message.register(cmd_delete_speaker, Command("delete_speaker"))
    dp.message.register(process_message_del)



