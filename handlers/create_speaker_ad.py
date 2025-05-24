import os
from aiogram import types, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv
from datacenter.db_manager import create_speaker, get_speaker_by_telegram_id, create_talk
import datetime
import logging

load_dotenv()
ORGANIZER_TELEGRAM_ID = int(os.getenv('ORGANIZER_TELEGRAM_ID'))


class CreateSpeakerState(StatesGroup):
    """Состояния для создания спикера"""
    waiting_for_speaker_id = State()
    waiting_for_speaker_name = State()
    waiting_for_talk_title = State()
    waiting_for_start_time = State()
    waiting_for_end_time = State()


async def cmd_add_speaker(message: types.Message, state: FSMContext):
    """Команда для добавления спикера"""
    if message.from_user.id != ORGANIZER_TELEGRAM_ID:
        await message.answer("Извините, у вас нет прав для выполнения этой команды.")
        return

    await message.answer("Введите Telegram ID спикера (только цифры):")
    await state.set_state(CreateSpeakerState.waiting_for_speaker_id)


async def process_speaker_id(message: types.Message, state: FSMContext):
    """Обработка ввода Telegram ID спикера"""
    speaker_id_str = message.text.strip()

    if not speaker_id_str.isdigit():
        await message.answer("ID должен содержать только цифры. Попробуйте еще раз:")
        return

    speaker_id = int(speaker_id_str)
    existing_speaker = get_speaker_by_telegram_id(speaker_id)

    if existing_speaker:
        await message.answer(f"Спикер с Telegram ID {speaker_id} уже существует в базе: {existing_speaker.name}")
        await state.clear()
        return

    await state.update_data(speaker_id=speaker_id)
    await message.answer("Введите фамилию и имя спикера:")
    await state.set_state(CreateSpeakerState.waiting_for_speaker_name)


async def process_speaker_name(message: types.Message, state: FSMContext):
    """Обработка ввода имени спикера"""
    speaker_name = message.text.strip()

    if not speaker_name:
        await message.answer("Имя не может быть пустым. Пожалуйста, введите фамилию и имя спикера:")
        return

    await state.update_data(speaker_name=speaker_name)
    await message.answer("Введите название доклада:")
    await state.set_state(CreateSpeakerState.waiting_for_talk_title)


async def process_talk_title(message: types.Message, state: FSMContext):
    """Обработка ввода названия доклада"""
    talk_title = message.text.strip()

    if not talk_title:
        await message.answer("Название доклада не может быть пустым. Пожалуйста, введите название доклада:")
        return

    await state.update_data(talk_title=talk_title)
    await message.answer("Введите время начала доклада в формате ГГГГ-ММ-ДД ЧЧ:ММ (например, 2024-12-25 14:00):")
    await state.set_state(CreateSpeakerState.waiting_for_start_time)


async def process_start_time(message: types.Message, state: FSMContext):
    """Обработка ввода времени начала доклада"""
    start_time_str = message.text.strip()

    try:
        start_time = datetime.datetime.strptime(start_time_str, '%Y-%m-%d %H:%M')
    except ValueError:
        await message.answer(
            "Неверный формат времени. Пожалуйста, введите время в формате ГГГГ-ММ-ДД ЧЧ:ММ (например, 2024-12-25 14:00):")
        return

    await state.update_data(start_time=start_time)
    await message.answer("Введите время окончания доклада в формате ГГГГ-ММ-ДД ЧЧ:ММ (например, 2024-12-25 15:00):")
    await state.set_state(CreateSpeakerState.waiting_for_end_time)


async def process_end_time(message: types.Message, state: FSMContext):
    """Обработка ввода времени окончания доклада"""
    end_time_str = message.text.strip()

    try:
        end_time = datetime.datetime.strptime(end_time_str, '%Y-%m-%d %H:%M')
    except ValueError:
        await message.answer(
            "Неверный формат времени. Пожалуйста, введите время в формате ГГГГ-ММ-ДД ЧЧ:ММ (например, 2024-12-25 15:00):")
        return

    data = await state.get_data()
    start_time = data['start_time']

    if end_time <= start_time:
        await message.answer(
            "Время окончания должно быть позже времени начала. Пожалуйста, введите корректное время окончания:")
        return

    # Получаем все данные
    speaker_id = data['speaker_id']
    speaker_name = data['speaker_name']
    talk_title = data['talk_title']

    try:
        # Создаем спикера
        speaker = create_speaker(name=speaker_name, telegram_id=speaker_id)
        if not speaker:
            await message.answer("Произошла ошибка при добавлении спикера. Возможно, такой ID уже существует.")
            await state.clear()
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
            await state.clear()
            return

        await message.answer(
            f"✅ Спикер '{speaker_name}' с докладом '{talk_title}' успешно добавлен.\n"
            f"🕒 Время доклада: с {start_time.strftime('%Y-%m-%d %H:%M')} по {end_time.strftime('%Y-%m-%d %H:%M')}."
        )

        # Уведомляем спикера
        try:
            await message.bot.send_message(
                chat_id=speaker_id,
                text=(
                    f"👋 Здравствуйте, {speaker_name}!\n\n"
                    f"🎤 Вас добавили в список спикеров на мероприятии.\n"
                    f"📋 Ваш доклад: {talk_title}\n"
                    f"🕒 Время выступления: с {start_time.strftime('%Y-%m-%d %H:%M')} по {end_time.strftime('%Y-%m-%d %H:%M')}.\n\n"
                    f"Удачи с выступлением! 🚀"
                )
            )
        except Exception as e:
            logging.warning(f"Не удалось отправить уведомление спикеру {speaker_id}: {e}")
            await message.answer("⚠️ Спикер добавлен, но уведомление не доставлено.")

    except Exception as e:
        logging.error(f"Ошибка при создании спикера/доклада: {e}")
        await message.answer("❌ Произошла ошибка при сохранении данных. Попробуйте еще раз.")

    await state.clear()


def register_create_speaker_ad_handlers(dp: Dispatcher):
    """Регистрация обработчиков создания спикера"""
    dp.message.register(cmd_add_speaker, Command("add_speaker"))
    dp.message.register(process_speaker_id, CreateSpeakerState.waiting_for_speaker_id)
    dp.message.register(process_speaker_name, CreateSpeakerState.waiting_for_speaker_name)
    dp.message.register(process_talk_title, CreateSpeakerState.waiting_for_talk_title)
    dp.message.register(process_start_time, CreateSpeakerState.waiting_for_start_time)
    dp.message.register(process_end_time, CreateSpeakerState.waiting_for_end_time)



