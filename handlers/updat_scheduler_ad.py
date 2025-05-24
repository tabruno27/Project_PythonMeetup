import os
from aiogram import types, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv
from datacenter.db_manager import update_talk, get_talks_by_speaker, get_speaker_by_id, get_speaker_by_telegram_id, get_all_participants, get_talk_by_id
import datetime
import logging


load_dotenv()
ORGANIZER_TELEGRAM_ID = int(os.getenv('ORGANIZER_TELEGRAM_ID'))

class UpdateScheduleState(StatesGroup):
    """Состояния для обновления расписания"""
    waiting_for_speaker_id = State()
    waiting_for_talk_id = State()
    waiting_for_title = State()
    waiting_for_start_time = State()
    waiting_for_end_time = State()


async def cmd_update_schedule(message: types.Message, state: FSMContext):
    """Команда для обновления расписания"""
    user_id = message.from_user.id

    logging.info(f"Команда /update_schedule от пользователя {user_id}")

    if user_id != ORGANIZER_TELEGRAM_ID:
        await message.answer("❌ Извините, у вас нет прав для выполнения этой команды.")
        return

    await message.answer("Введите Telegram ID спикера, чью программу вы хотите обновить:")
    await state.set_state(UpdateScheduleState.waiting_for_speaker_id)
    logging.info(f"Установлено состояние ожидания ID спикера для обновления для пользователя {user_id}")


async def process_update_speaker_id(message: types.Message, state: FSMContext):
    """Обработка ввода Telegram ID спикера"""
    telegram_id_str = message.text.strip()

    if not telegram_id_str.isdigit():
        await message.answer("Telegram ID должен содержать только цифры. Попробуйте еще раз:")
        return

    telegram_id = int(telegram_id_str)
    speaker = get_speaker_by_telegram_id(telegram_id)

    if not speaker:
        await message.answer(f"❌ Спикер с Telegram ID {telegram_id} не найден. Попробуйте еще раз:")
        return

    # Получаем расписание спикера
    speaker_id = speaker.id
    talks = get_talks_by_speaker(speaker_id)
    if not talks:
        await message.answer(f"❌ У спикера {speaker.name} нет запланированных докладов.")
        await state.clear()
        return

    # Отправляем расписание спикера
    schedule_message = "\n".join([
        f"ID {talk.id}: '{talk.title}' с {talk.start_time.strftime('%Y-%m-%d %H:%M')} до {talk.end_time.strftime('%Y-%m-%d %H:%M')}"
        for talk in talks
    ])

    await message.answer(
        f"📋 Расписание спикера {speaker.name}:\n\n{schedule_message}\n\n"
        "Введите ID доклада, который хотите обновить:"
    )

    await state.update_data(speaker_id=speaker_id)
    await state.set_state(UpdateScheduleState.waiting_for_talk_id)


async def process_update_talk_id(message: types.Message, state: FSMContext):
    """Обработка ввода ID доклада"""
    talk_id_str = message.text.strip()

    if not talk_id_str.isdigit():
        await message.answer("ID должен содержать только цифры. Попробуйте еще раз:")
        return

    talk_id = int(talk_id_str)
    talk = get_talk_by_id(talk_id)
    data = await state.get_data()

    if not talk or talk.speaker.id != data['speaker_id']:
        await message.answer("❌ Доклад с таким ID не найден или он не принадлежит этому спикеру. Попробуйте еще раз:")
        return

    await message.answer("Введите новое название доклада:")
    await state.update_data(talk_id=talk_id)
    await state.set_state(UpdateScheduleState.waiting_for_title)


async def process_update_title(message: types.Message, state: FSMContext):
    """Обработка ввода нового названия"""
    new_title = message.text.strip()

    if not new_title:
        await message.answer("Название не может быть пустым. Попробуйте еще раз:")
        return

    await state.update_data(new_title=new_title)
    await message.answer("Введите новое время начала в формате ГГГГ-ММ-ДД ЧЧ:ММ (например, 25.05.2025 14:00):")
    await state.set_state(UpdateScheduleState.waiting_for_start_time)


async def process_update_start_time(message: types.Message, state: FSMContext):
    """Обработка ввода нового времени начала"""
    new_start_time_str = message.text.strip()

    try:
        new_start_time = datetime.datetime.strptime(new_start_time_str, "%d.%m.%Y %H:%M")
    except ValueError:
        await message.answer(
            "❌ Неверный формат времени. Введите в формате ДД.ММ.ГГГГ ЧЧ:ММ (например, 25.05.2025 14:00):")
        return

    await state.update_data(new_start_time=new_start_time)
    await message.answer("Введите новое время окончания в формате ДД.ММ.ГГГГ ЧЧ:ММ (например, 25.05.2025 15:00):")
    await state.set_state(UpdateScheduleState.waiting_for_end_time)


async def process_update_end_time(message: types.Message, state: FSMContext):
    """Обработка ввода нового времени окончания"""
    new_end_time_str = message.text.strip()

    try:
        new_end_time = datetime.datetime.strptime(new_end_time_str, "%d.%m.%Y %H:%M")
    except ValueError:
        await message.answer(
            "❌ Неверный формат времени. Введите в формате ДД.ММ.ГГГГ ЧЧ:ММ (например, 25.05.2025 15:00):")
        return

    data = await state.get_data()
    new_start_time = data['new_start_time']

    if new_end_time <= new_start_time:
        await message.answer("❌ Время окончания должно быть позже времени начала. Попробуйте еще раз:")
        return

    # Получаем все данные
    talk_id = data['talk_id']
    new_title = data['new_title']

    try:
        # Обновляем доклад в базе данных
        updated_talk = update_talk(
            talk_id,
            new_title=new_title,
            new_start_time=new_start_time,
            new_end_time=new_end_time
        )

        if updated_talk:
            await message.answer(
                f"✅ Программа успешно обновлена!\n\n"
                f"📋 Доклад: {new_title}\n"
                f"🕒 Новое время: {new_start_time.strftime('%d.%m.%Y %H:%M')} - {new_end_time.strftime('%d.%m.%Y %H:%M')}"
            )

            # Уведомляем всех участников
            await notify_participants(message, updated_talk)
        else:
            await message.answer("❌ Произошла ошибка при обновлении программы. Попробуйте еще раз.")

    except Exception as e:
        logging.error(f"Ошибка при обновлении расписания: {e}")
        await message.answer("❌ Произошла ошибка при обновлении. Попробуйте позже.")

    await state.clear()


async def notify_participants(message: types.Message, talk):
    """Уведомление участников об обновлении программы"""
    try:
        participants = get_all_participants()

        if not participants:
            return

        start_time_str = talk.start_time.strftime('%d.%m.%Y %H:%M')
        end_time_str = talk.end_time.strftime('%d.%m.%Y %H:%M')

        notification_text = (
            f"📢 Программа обновлена!\n\n"
            f"🗣 Доклад: {talk.title}\n"
            f"👤 Спикер: {talk.speaker.name}\n"
            f"🕒 Время: {start_time_str} - {end_time_str}\n\n"
            f"Не пропустите! 🚀"
        )

        for participant in participants:
            try:
                await message.bot.send_message(
                    chat_id=participant["telegram_id"],
                    text=notification_text
                )
            except Exception as e:
                logging.warning(f"Не удалось отправить уведомление участнику {participant['telegram_id']}: {e}")

    except Exception as e:
        logging.error(f"Ошибка при отправке уведомлений: {e}")


def register_up_sheduler_handlers(dp: Dispatcher):
    """Регистрация обработчиков обновления расписания"""
    dp.message.register(cmd_update_schedule, Command("update_schedule"))
    dp.message.register(process_update_speaker_id, UpdateScheduleState.waiting_for_speaker_id)
    dp.message.register(process_update_talk_id, UpdateScheduleState.waiting_for_talk_id)
    dp.message.register(process_update_title, UpdateScheduleState.waiting_for_title)
    dp.message.register(process_update_start_time, UpdateScheduleState.waiting_for_start_time)
    dp.message.register(process_update_end_time, UpdateScheduleState.waiting_for_end_time)
