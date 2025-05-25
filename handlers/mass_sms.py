import os
from aiogram import types, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv
from datacenter.db_manager import get_all_participants
import logging

load_dotenv()
ORGANIZER_TELEGRAM_ID = int(os.getenv('ORGANIZER_TELEGRAM_ID'))

class MassSmsState(StatesGroup):
    """Состояния для массовой рассылки"""
    waiting_for_message = State()

async def cmd_mass_sms(message: types.Message, state: FSMContext):
    """Команда для начала массовой рассылки"""
    user_id = message.from_user.id

    logging.info(f"Команда /mass_sms от пользователя {user_id}")

    if user_id != ORGANIZER_TELEGRAM_ID:
        await message.answer("❌ Извините, у вас нет прав для выполнения этой команды.")
        return

    await message.answer("Введите текст для массовой рассылки:")
    await state.set_state(MassSmsState.waiting_for_message)
    logging.info(f"Установлено состояние ожидания текста сообщения для пользователя {user_id}")

async def process_mass_sms(message: types.Message, state: FSMContext):
    """Обработка текста сообщения для массовой рассылки"""
    user_id = message.from_user.id

    logging.info(f"Получен текст для массовой рассылки от пользователя {user_id}")

    # Получаем текст сообщения
    sms_text = message.text

    # Получаем список участников
    participants = get_all_participants()

    if not participants:
        await message.answer("📭 У нас нет участников для рассылки.")
        await state.clear()
        return

    # Отправляем сообщение каждому участнику
    for participant in participants:
        try:
            await message.bot.send_message(
                chat_id=participant["telegram_id"],
                text=sms_text
            )
            logging.info(f"Сообщение отправлено участнику {participant['telegram_id']}")
        except Exception as e:
            logging.warning(f"Не удалось отправить сообщение участнику {participant['telegram_id']}: {e}")

    await message.answer("✅ Рассылка завершена!")
    await state.clear()

def register_mass_sms_handlers(dp: Dispatcher):
    """Регистрация обработчиков массовой рассылки"""
    dp.message.register(cmd_mass_sms, Command("mass_sms"))
    dp.message.register(process_mass_sms, MassSmsState.waiting_for_message)
