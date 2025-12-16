import json
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date

# Инициализируем db здесь, а в app.py вызываем db.init_app(app)
db = SQLAlchemy()


class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Practice(db.Model):
    __tablename__ = "practice"

    id = db.Column(db.Integer, primary_key=True)

    # ТЕКУЩАЯ ЛОГИКА ПРИЛОЖЕНИЯ (используется в app.py и шаблонах)
    title = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.String(500))
    quote = db.Column(db.String(500))
    form_schema_json = db.Column(db.Text)

    # ЗАЧАТКИ НОВОЙ КОНЦЕПЦИИ (можем использовать позже, не ломая старое)
    color = db.Column(db.String(20))
    category = db.Column(db.String(50))
    difficulty = db.Column(db.Integer)
    motivation = db.Column(db.Text)

    # Записи по практике (для старой логики форм)
    entries = db.relationship("PracticeEntry", backref="practice", cascade="all, delete-orphan")

    # Примеры и подсказки (для новой системы практик — пока не используются в app.py)
    examples = db.relationship("PracticeExample", backref="practice", cascade="all, delete-orphan")
    tips = db.relationship("PracticeTip", backref="practice", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Practice {self.title}>"


class PracticeEntry(db.Model):
    __tablename__ = "practice_entry"

    id = db.Column(db.Integer, primary_key=True)
    practice_id = db.Column(db.Integer, db.ForeignKey("practice.id"), nullable=False)
    entry_date = db.Column(db.String(20), nullable=False)
    fields_json = db.Column(db.Text)

    @property
    def fields(self):
        if not self.fields_json:
            return {}
        return json.loads(self.fields_json)

    def __repr__(self):
        return f"<PracticeEntry practice_id={self.practice_id} date={self.entry_date}>"


def init_practices():
    """Создаёт базовые практики, если их нет."""
    if Practice.query.count() > 0:
        return

    practices = [
        Practice(
            title="Осознанность",
            description="Эта практика помогает выйти из автоматизма...",
            quote="Ты становишься тем, на что направляешь внимание.",
            form_schema_json=json.dumps([
                {"key": "reflection", "label": "Что ты заметил?", "type": "text"},
                {"key": "emotion", "label": "Какие эмоции возникли?", "type": "text"},
            ], ensure_ascii=False)
        ),
        Practice(
            title="Благодарность",
            description="Практика благодарности переключает внимание...",
            quote="Благодарность — это магнит для хорошего.",
            form_schema_json=json.dumps([
                {"key": "item1", "label": "Благодарность №1", "type": "text"},
                {"key": "item2", "label": "Благодарность №2", "type": "text"},
                {"key": "item3", "label": "Благодарность №3", "type": "text"},
            ], ensure_ascii=False)
        ),
        Practice(
            title="Цель дня",
            description="Одна чёткая цель на день создаёт ясность...",
            quote="Фокус создаёт результат.",
            form_schema_json=json.dumps([
                {"key": "goal", "label": "Главная цель дня", "type": "text"},
            ], ensure_ascii=False)
        ),
    ]

    db.session.add_all(practices)
    db.session.commit()


class PracticeExample(db.Model):
    __tablename__ = "practice_example"

    id = db.Column(db.Integer, primary_key=True)
    practice_id = db.Column(db.Integer, db.ForeignKey("practice.id"), nullable=False)
    text = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"<PracticeExample {self.text[:20]}>"


class PracticeTip(db.Model):
    __tablename__ = "practice_tip"

    id = db.Column(db.Integer, primary_key=True)
    practice_id = db.Column(db.Integer, db.ForeignKey("practice.id"), nullable=False)
    text = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"<PracticeTip {self.text[:20]}>"


class PracticeDailyStatus(db.Model):
    __tablename__ = "practice_daily_status"

    id = db.Column(db.Integer, primary_key=True)

    # Авторизация отключена, но поле оставляем для будущего
    user_id = db.Column(db.Integer, nullable=False, default=1)

    practice_id = db.Column(db.Integer, db.ForeignKey("practice.id"), nullable=False)

    date = db.Column(db.Date, nullable=False, default=date.today)

    completed = db.Column(db.Boolean, default=False)

    streak = db.Column(db.Integer, default=0)

    progress_14 = db.Column(db.Integer, default=0)
    progress_30 = db.Column(db.Integer, default=0)
    progress_60 = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<DailyStatus practice={self.practice_id} date={self.date} completed={self.completed}>"
