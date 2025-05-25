from aiogram import Dispatcher
from .scheduler import register_scheduler_handlers
from .questions import register_question_handlers
from .start import register_start_handlers
from .active import register_active_handlers
from .create_speaker_ad import register_create_speaker_ad_handlers
from .delete_speaker_ad import register_delete_speaker_ad_handlers
from .updat_scheduler_ad import register_up_sheduler_handlers
from .my_questions import register_my_questions_handlers
from .talk_control import register_talk_control_handlers
from .donate import register_donate_handlers

def register_all_handlers(dp: Dispatcher):
    register_start_handlers(dp)
    register_scheduler_handlers(dp)
    register_question_handlers(dp)
    register_active_handlers(dp)
    register_create_speaker_ad_handlers(dp)
    register_delete_speaker_ad_handlers(dp)
    register_up_sheduler_handlers(dp)
    register_my_questions_handlers(dp)
    register_talk_control_handlers(dp)
    register_donate_handlers(dp)
