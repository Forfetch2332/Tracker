import json
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

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
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500))
    quote = db.Column(db.String(500))
    form_schema_json = db.Column(db.Text)


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


def init_practices():
    """Создаёт практики, если их нет."""
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
