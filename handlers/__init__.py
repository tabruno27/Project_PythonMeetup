from aiogram import Dispatcher
from .scheduler import register_scheduler_handlers


def register_all_handlers(dp: Dispatcher):
    register_scheduler_handlers(dp)