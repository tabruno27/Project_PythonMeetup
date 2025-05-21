import datetime
from peewee import *
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_DIR / 'meetup.db'
db = SqliteDatabase(DB_PATH)


class BaseModel(Model):
    class Meta:
        database = db


class Speaker(BaseModel):
    name = CharField()
    telegram_id = BigIntegerField(unique=True)

    def __str__(self):
        return self.name


class Talk(BaseModel):
    speaker = ForeignKeyField(Speaker, backref='talks', on_delete='CASCADE')
    title = CharField()
    start_time = DateTimeField()
    end_time = DateTimeField()

    def __str__(self):
        return f"'{self.title}' by {self.speaker.name}"


class Question(BaseModel):
    talk = ForeignKeyField(Talk, backref='questions', on_delete='CASCADE')
    guest_telegram_id = BigIntegerField()
    text = TextField()
    timestamp = DateTimeField(default=datetime.datetime.now)
    answered = BooleanField(default=False)

    def __str__(self):
        return f"Вопрос к '{self.talk.title}': {self.text[:50]}..."


def connect_db():
    if db.is_closed():
        db.connect()


def close_db():
    if not db.is_closed():
        db.close()


def create_tables():
    connect_db()
    db.create_tables([Speaker, Talk, Question], safe=True)
    close_db()


def create_speaker(name: str, telegram_id: int) -> Speaker | None:
    try:
        with db.atomic():
            speaker = Speaker.create(name=name, telegram_id=telegram_id)
            return speaker
    except IntegrityError:
        print(f"Ошибка: Спикер с Telegram ID {telegram_id} уже существует.")
        return None


def get_speaker_by_id(speaker_id: int) -> Speaker | None:
    with db.atomic():
        speaker = Speaker.get_or_none(Speaker.id == speaker_id)
        return speaker


def get_speaker_by_telegram_id(telegram_id: int) -> Speaker | None:
    with db.atomic():
        speaker = Speaker.get_or_none(Speaker.telegram_id == telegram_id)
        return speaker


def get_all_speakers() -> list[Speaker]:
    with db.atomic():
        speakers = list(Speaker.select())
        return speakers


def update_speaker(speaker_id: int, new_name: str = None, new_telegram_id: int = None) -> Speaker | None:
    with db.atomic():
        speaker = Speaker.get_or_none(Speaker.id == speaker_id)
        if speaker:
            if new_name:
                speaker.name = new_name
            if new_telegram_id:
                try:
                    speaker.telegram_id = new_telegram_id
                except IntegrityError:
                    print(f"Ошибка: Telegram ID {new_telegram_id} уже занят.")
                    return None
            speaker.save()

        return speaker


def delete_speaker(speaker_id: int) -> bool:
    with db.atomic(): # Используем db.atomic для транзакции
        query = Speaker.delete().where(Speaker.id == speaker_id)
        rows_deleted = query.execute()
        return rows_deleted > 0


def create_talk(speaker_id: int, title: str, start_time: datetime.datetime, end_time: datetime.datetime) -> Talk | None:
    speaker = get_speaker_by_id(speaker_id)
    if not speaker:
        print(f"Ошибка: Спикер с ID {speaker_id} не найден для создания доклада.")
        return None
    with db.atomic():
        talk = Talk.create(speaker=speaker_id, title=title, start_time=start_time, end_time=end_time)
        return talk


def get_talk_by_id(talk_id: int) -> Talk | None:
    with db.atomic():
        talk = Talk.get_or_none(Talk.id == talk_id)
        return talk


def get_talks_by_speaker(speaker_id: int) -> list[Talk]:
    with db.atomic():
        talks = list(Talk.select().where(Talk.speaker == speaker_id).order_by(Talk.start_time))
        return talks


def update_talk(talk_id: int, new_title: str = None, new_start_time: datetime.datetime = None, new_end_time: datetime.datetime = None) -> Talk | None:
    with db.atomic():
        talk = Talk.get_or_none(Talk.id == talk_id)
        if talk:
            if new_title:
                talk.title = new_title
            if new_start_time:
                talk.start_time = new_start_time
            if new_end_time:
                talk.end_time = new_end_time
            talk.save()
        return talk


def delete_talk(talk_id: int) -> bool:
    with db.atomic():
        query = Talk.delete().where(Talk.id == talk_id)
        rows_deleted = query.execute()
        return rows_deleted > 0


def get_current_talk() -> Talk | None:
    with db.atomic():
        now = datetime.datetime.now()
        talk = Talk.get_or_none(
            (Talk.start_time <= now) & (Talk.end_time >= now)
        )
        return talk


def get_all_talks() -> list[Talk]:
    with db.atomic():
        talks = list(Talk.select().order_by(Talk.start_time.asc(), Talk.end_time.asc()))
        return talks


def create_question(talk_id: int, guest_telegram_id: int, text: str) -> Question | None:
    talk = get_talk_by_id(talk_id)
    if not talk:
        print(f"Ошибка: Доклад с ID {talk_id} не найден для создания вопроса.")
        return None
    with db.atomic():
        question = Question.create(talk=talk_id, guest_telegram_id=guest_telegram_id, text=text)
        return question


def get_question_by_id(question_id: int) -> Question | None:
    with db.atomic():
        question = Question.get_or_none(Question.id == question_id)
        return question


def get_questions_for_talk(talk_id: int, answered_only: bool = False, unanswered_only: bool = False) -> list[Question]:
    with db.atomic():
        query = Question.select().where(Question.talk == talk_id)
        if answered_only:
            query = query.where(Question.answered == True)
        elif unanswered_only:
            query = query.where(Question.answered == False)
        questions = list(query.order_by(Question.timestamp))
        return questions


def mark_question_as_answered(question_id: int) -> Question | None:
    with db.atomic():
        question = Question.get_or_none(Question.id == question_id)
        if question:
            question.answered = True
            question.save()
        return question


def get_all_questions() -> list[Question]:
    with db.atomic():
        questions = list(Question.select().order_by(Question.timestamp))
        return questions


def delete_question(question_id: int) -> bool:
    with db.atomic():
        rows_deleted = Question.delete().where(Question.id == question_id).execute()
        return rows_deleted > 0
