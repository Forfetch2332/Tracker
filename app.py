import os
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from flask import Flask, render_template, url_for, redirect, jsonify
from flask_migrate import Migrate

from models import db, Practice, PracticeDailyStatus, Hint, Example

# ---------------------------------------------------------
# Инициализация приложения
# ---------------------------------------------------------

app = Flask(__name__)
load_dotenv()

app.config["SECRET_KEY"] = "super-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
migrate = Migrate(app, db)


# ---------------------------------------------------------
# Мотивационный блок
# ---------------------------------------------------------

def generate_motivation(statuses, practices):
    completed_count = sum(1 for s in statuses.values() if s.completed)
    total = len(practices)

    if completed_count == 0:
        return "Начни с самой простой практики — движение запускается с первого шага."

    if completed_count == 1:
        return "Отлично. Одна практика — это уже точка опоры. Закрепи её."

    if total > 0 and completed_count >= total * 0.5 and completed_count < total:
        return "Ты уже в процессе. Держи темп — прогресс строится на повторении."

    if total > 0 and completed_count == total:
        return "Сегодня ты закрыл весь список. Это и есть дисциплина в действии."

    max_streak = max((s.streak for s in statuses.values()), default=0)

    if max_streak >= 7:
        return f"Серия {max_streak} дней — это уже привычка. Продолжай укреплять."

    if max_streak >= 3:
        return f"Серия {max_streak} дней — хороший старт. Не обрывай ритм."

    return "Каждое выполненное действие — кирпич в твою систему. Продолжай."


# ---------------------------------------------------------
# Маршруты
# ---------------------------------------------------------

@app.route("/")
def welcome_page():
    return render_template(
        "welcome.html",
        today=url_for("today_page"),
        practices=url_for("practice_list_page"),
        guide=url_for("guide_page"),
    )


@app.route("/today")
def today_page():
    today = date.today()

    practices = Practice.query.all()

    statuses = {
        s.practice_id: s
        for s in PracticeDailyStatus.query.filter_by(
            user_id=1,
            date=today
        ).all()
    }

    hints = Hint.query.all()
    examples = Example.query.all()

    hint_of_day = hints[today.toordinal() % len(hints)] if hints else None
    example_of_day = examples[today.toordinal() % len(examples)] if examples else None

    motivation = generate_motivation(statuses, practices)

    return render_template(
        "today.html",
        practices=practices,
        statuses=statuses,
        hint_of_day=hint_of_day,
        example_of_day=example_of_day,
        motivation=motivation
    )


@app.route("/guide")
def guide_page():
    practices = Practice.query.all()
    return render_template("guide.html", practices=practices)


@app.route("/practices")
def practice_list_page():
    practices = Practice.query.all()
    return render_template("practice_list.html", practices=practices)


@app.route("/practice/<int:pid>/toggle", methods=["POST"])
def toggle_practice(pid):
    today = date.today()

    status = PracticeDailyStatus.query.filter_by(
        user_id=1,
        practice_id=pid,
        date=today
    ).first()

    # Создаём статус, если его нет
    if not status:
        status = PracticeDailyStatus(
            user_id=1,
            practice_id=pid,
            date=today,
            completed=True
        )
        db.session.add(status)
        db.session.commit()

    else:
        status.completed = not status.completed
        db.session.commit()

    # Пересчёт streak
    if status.completed:
        yesterday = today - timedelta(days=1)

        prev = PracticeDailyStatus.query.filter_by(
            user_id=1,
            practice_id=pid,
            date=yesterday,
            completed=True
        ).first()

        status.streak = (prev.streak + 1) if prev else 1
    else:
        status.streak = 0

    # Прогресс 14/30/60
    s = status.streak
    status.progress_14 = min(int(s / 14 * 100), 100)
    status.progress_30 = min(int(s / 30 * 100), 100)
    status.progress_60 = min(int(s / 60 * 100), 100)

    db.session.commit()

    return jsonify({
        "completed": status.completed,
        "streak": status.streak,
        "progress_14": status.progress_14,
        "progress_30": status.progress_30,
        "progress_60": status.progress_60,
        "practice_id": pid
    })


# ---------------------------------------------------------
# Контекстные процессоры
# ---------------------------------------------------------

@app.context_processor
def inject_year():
    return {"current_year": datetime.now().year}


# ---------------------------------------------------------
# Запуск
# ---------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
