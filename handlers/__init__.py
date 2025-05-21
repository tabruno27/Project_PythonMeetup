from aiogram import Dispatcher
from .scheduler import register_scheduler_handlers
from .questions import register_question_handlers
from .start import register_start_handlers
from .active import register_active_handlers

def register_all_handlers(dp: Dispatcher):
    register_start_handlers(dp)
    register_scheduler_handlers(dp)
    register_question_handlers(dp)
    register_active_handlers(dp)