import os
from aiogram import types, Dispatcher
from aiogram.filters import Command
from dotenv import load_dotenv
from datacenter.db_manager import get_speaker_by_telegram_id, get_talks_by_speaker, get_talk_by_id, update_talk, \
    get_all_participants
import logging

load_dotenv()
ORGANIZER_TELEGRAM_ID = int(os.getenv('ORGANIZER_TELEGRAM_ID'))


active_talk_id = None


def is_talk_active():
    return active_talk_id is not None


def get_active_talk_id():
    return active_talk_id


async def handle_start_talk(message: types.Message):
    global active_talk_id

    user_id = message.from_user.id

    speaker = get_speaker_by_telegram_id(user_id)

    if not speaker:
        await message.answer("❌ Только зарегистрированные спикеры могут начинать доклады.")
        return

    if is_talk_active():
        active_talk = get_talk_by_id(active_talk_id)
        if active_talk and active_talk.speaker.id == speaker.id:
            await message.answer(
                f"❗️ У вас уже есть активный доклад: '{active_talk.title}'.\nЗавершите его командой /end_talk перед началом нового.")
        else:
            await message.answer("❌ В данный момент уже идёт другой доклад. Подождите его завершения.")
        return

    talks = get_talks_by_speaker(speaker.id)

    if not talks:
        await message.answer(f"👋 {speaker.name}, у вас нет запланированных докладов.")
        return

    if len(talks) == 1:
        active_talk_id = talks[0].id
        await message.answer(
            f"✅ Доклад '{talks[0].title}' начат!\nСлушатели могут задавать вопросы с помощью команды /ask\nДля завершения доклада используйте команду /end_talk")

        await notify_participants_start(message.bot, talks[0])
    else:
        talk_list = "\n".join([f"{i + 1}. {talk.title}" for i, talk in enumerate(talks)])
        await message.answer(
            f"👋 {speaker.name}, у вас несколько докладов. Укажите номер доклада, который хотите начать:\n\n{talk_list}\n\n"
            "Например, введите: /start_talk 1"
        )

        command_parts = message.text.split()
        if len(command_parts) == 2 and command_parts[1].isdigit():
            talk_number = int(command_parts[1]) - 1
            if 0 <= talk_number < len(talks):
                active_talk_id = talks[talk_number].id
                await message.answer(
                    f"✅ Доклад '{talks[talk_number].title}' начат!\nСлушатели могут задавать вопросы с помощью команды /ask\nДля завершения доклада используйте команду /end_talk")

                await notify_participants_start(message.bot, talks[talk_number])
            else:
                await message.answer("❌ Неверный номер доклада. Пожалуйста, выберите из списка.")


async def handle_end_talk(message: types.Message):
    global active_talk_id

    user_id = message.from_user.id

    speaker = get_speaker_by_telegram_id(user_id)

    if not speaker:
        await message.answer("❌ Только зарегистрированные спикеры могут завершать доклады.")
        return


    if not is_talk_active():
        await message.answer("❌ В данный момент нет активного доклада.")
        return


    active_talk = get_talk_by_id(active_talk_id)

    if active_talk.speaker.id != speaker.id:
        await message.answer("❌ Вы не можете завершить чужой доклад.")
        return


    talk_title = active_talk.title
    await notify_participants_end(message.bot, active_talk)
    active_talk_id = None

    await message.answer(f"✅ Доклад '{talk_title}' завершен!")


async def notify_participants_start(bot, talk):
    try:
        participants = get_all_participants()
        if not participants:
            return

        notification_text = (
            f"🎬 Внимание! Начался доклад!\n\n"
            f"🗣 Тема: {talk.title}\n"
            f"👤 Спикер: {talk.speaker.name}\n\n"
            f"Вы можете задавать вопросы спикеру с помощью команды /ask"
        )

        for participant in participants:
            if participant["telegram_id"] != talk.speaker.telegram_id:  # Не отправляем уведомление самому спикеру
                try:
                    await bot.send_message(
                        chat_id=participant["telegram_id"],
                        text=notification_text
                    )
                except Exception as e:
                    logging.warning(f"Не удалось отправить уведомление участнику {participant['telegram_id']}: {e}")

    except Exception as e:
        logging.error(f"Ошибка при отправке уведомлений о начале доклада: {e}")


async def notify_participants_end(bot, talk):
    try:
        participants = get_all_participants()
        if not participants:
            return

        notification_text = (
            f"🏁 Доклад завершен!\n\n"
            f"🗣 Тема: {talk.title}\n"
            f"👤 Спикер: {talk.speaker.name}\n\n"
            f"Благодарим за участие!"
        )

        for participant in participants:
            if participant["telegram_id"] != talk.speaker.telegram_id:  # Не отправляем уведомление самому спикеру
                try:
                    await bot.send_message(
                        chat_id=participant["telegram_id"],
                        text=notification_text
                    )
                except Exception as e:
                    logging.warning(f"Не удалось отправить уведомление участнику {participant['telegram_id']}: {e}")

    except Exception as e:
        logging.error(f"Ошибка при отправке уведомлений о завершении доклада: {e}")


def register_talk_control_handlers(dp: Dispatcher):
    dp.message.register(handle_start_talk, Command("start_talk"))
    dp.message.register(handle_end_talk, Command("end_talk"))