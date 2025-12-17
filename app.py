import json
import os
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from flask import Flask, render_template, url_for, redirect, jsonify
from flask_migrate import Migrate

from models import db, Practice, PracticeDailyStatus


app = Flask(__name__)
load_dotenv()

app.config["SECRET_KEY"] = "super-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
migrate = Migrate(app, db)


# -----------------------------
# Маршруты (без авторизации)
# -----------------------------
@app.route("/")
def welcome_page():
    return render_template(
        "welcome.html",
        # можно оставить ссылки для навигации
        today=url_for("today_page"),
        practices=url_for("practice_list_page"),
        guide=url_for("guide_page"),
    )


@app.route("/today")
def today_page():
    practices = Practice.query.all()

    today = date.today()
    statuses = {
        s.practice_id: s
        for s in PracticeDailyStatus.query.filter_by(user_id=1, date=today).all()
    }

    return render_template("today.html", practices=practices, statuses=statuses)


@app.route("/guide")
def guide_page():
    """Гайд по практикам — список с описаниями."""
    practices = Practice.query.all()
    return render_template("guide.html", practices=practices)


@app.route("/practices")
def practice_list_page():
    """Список всех практик."""
    practices = Practice.query.all()
    return render_template("practice_list.html", practices=practices)




@app.route("/practice/<int:pid>/toggle", methods=["POST"])
def toggle_practice(pid):
    today = date.today()

    # Запись за сегодня
    status = PracticeDailyStatus.query.filter_by(
        user_id=1,
        practice_id=pid,
        date=today
    ).first()

    # Если ещё нет записи за сегодня — создаём
    if not status:
        status = PracticeDailyStatus(
            user_id=1,
            practice_id=pid,
            date=today,
            completed=True
        )
        db.session.add(status)
    else:
        # Переключаем состояние
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

    # Пересчёт прогресса
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




# -----------------------------
# Контекстные процессоры
# -----------------------------
@app.context_processor
def inject_year():
    return {"current_year": datetime.now().year}


if __name__ == "__main__":
    app.run(debug=True)
