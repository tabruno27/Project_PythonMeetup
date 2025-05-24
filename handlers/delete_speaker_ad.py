import os
from aiogram import types, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv
from db_manager import delete_speaker, get_speaker_by_id, get_speaker_by_telegram_id, delete_talk_by_speaker_id
import logging

load_dotenv()
ORGANIZER_TELEGRAM_ID = int(os.getenv('ORGANIZER_TELEGRAM_ID'))


class DeleteSpeakerState(StatesGroup):
    """Состояния для удаления спикера"""
    waiting_for_speaker_id = State()


async def cmd_delete_speaker(message: types.Message, state: FSMContext):
    """Команда для удаления спикера"""
    user_id = message.from_user.id

    logging.info(f"Команда /delete_speaker от пользователя {user_id}")

    if user_id != ORGANIZER_TELEGRAM_ID:
        await message.answer("❌ У вас нет прав на выполнение этой команды.")
        return

    await message.answer("Введите Telegram ID спикера, которого необходимо удалить:")
    await state.set_state(DeleteSpeakerState.waiting_for_speaker_id)
    logging.info(f"Установлено состояние ожидания ID спикера для пользователя {user_id}")


async def process_delete_speaker_id(message: types.Message, state: FSMContext):
    """Обработка ввода Telegram ID спикера для удаления"""
    telegram_id_str = message.text.strip()

    if not telegram_id_str.isdigit():
        await message.answer("Telegram ID должен содержать только цифры. Попробуйте еще раз:")
        return

    telegram_id = int(telegram_id_str)

    try:
        # Получаем информацию о спикере по Telegram ID
        speaker = get_speaker_by_telegram_id(telegram_id)
        if not speaker:
            await message.answer("❌ Спикер с таким Telegram ID не найден.")
            await state.clear()
            return

        speaker_name = speaker.name
        speaker_db_id = speaker.id

        # Удаляем все доклады спикера
        talks_deleted = delete_talk_by_speaker_id(speaker_db_id)

        # Удаляем спикера
        speaker_deleted = delete_speaker(speaker_db_id)

        if speaker_deleted:
            if talks_deleted > 0:
                await message.answer(
                    f"✅ Спикер '{speaker_name}' (Telegram ID: {telegram_id}) и его доклад(ы) ({talks_deleted} шт.) успешно удалены."
                )
            else:
                await message.answer(
                    f"✅ Спикер '{speaker_name}' (Telegram ID: {telegram_id}) успешно удален. У него не было докладов."
                )
        else:
            await message.answer("❌ Произошла ошибка при удалении спикера.")

    except Exception as e:
        logging.error(f"Ошибка при удалении спикера: {e}")
        await message.answer("❌ Произошла ошибка при удалении спикера. Попробуйте позже.")

    await state.clear()


def register_delete_speaker_ad_handlers(dp: Dispatcher):
    """Регистрация обработчиков удаления спикера"""
    dp.message.register(cmd_delete_speaker, Command("delete_speaker"))
    dp.message.register(process_delete_speaker_id, DeleteSpeakerState.waiting_for_speaker_id)



