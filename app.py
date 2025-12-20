import os
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from flask import Flask, render_template, url_for, redirect, jsonify, request
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

@app.route("/progress")
def progress_page():
    """
    Страница визуализации прогресса: выбор практики и график.
    """
    practices = Practice.query.all()
    practice_id = request.args.get("practice_id", type=int)
    selected = None
    if practice_id:
        selected = Practice.query.get(practice_id)
    return render_template(
        "progress.html",
        practices=practices,
        selected_practice=selected
    )


@app.route("/api/progress/<int:practice_id>")
def api_progress(practice_id):
    """
    JSON-данные для графика: последние 60 дней.
    """
    today = date.today()
    start = today - timedelta(days=59)

    statuses = (
        PracticeDailyStatus.query
        .filter(
            PracticeDailyStatus.user_id == 1,
            PracticeDailyStatus.practice_id == practice_id,
            PracticeDailyStatus.date >= start,
            PracticeDailyStatus.date <= today
        )
        .order_by(PracticeDailyStatus.date.asc())
        .all()
    )

    by_date = {s.date: s for s in statuses}

    dates, completed, streak = [], [], []
    current_streak = 0

    for i in range(60):
        dt = start + timedelta(days=i)
        dates.append(dt.isoformat())

        st = by_date.get(dt)
        if st and st.completed:
            completed.append(1)
            current_streak = st.streak if st.streak is not None else current_streak + 1
        else:
            completed.append(0)
            current_streak = 0

        streak.append(current_streak)

    return jsonify({
        "practice_id": practice_id,
        "dates": dates,
        "completed": completed,
        "streak": streak
    })
@app.route("/analytics")
def analytics_page():
    practices = Practice.query.all()

    # Преобразуем объекты Practice в словари для JSON
    practices_data = [
        {
            "id": p.id,
            "title": p.title,
            "color": p.color
        }
        for p in practices
    ]

    return render_template(
        "analytics.html",
        practices=practices,          # для цикла {% for practice in practices %}
        practices_data=practices_data # для передачи в JS
    )


@app.route("/history")
def history_page():
    today = date.today()
    start = today - timedelta(days=29)

    statuses = (
        db.session.query(PracticeDailyStatus, Practice)
        .join(Practice, PracticeDailyStatus.practice_id == Practice.id)
        .filter(
            PracticeDailyStatus.user_id == 1,
            PracticeDailyStatus.date >= start,
            PracticeDailyStatus.date <= today
        )
        .order_by(PracticeDailyStatus.date.desc())
        .all()
    )

    history = {}
    for s, p in statuses:
        history.setdefault(s.date, []).append({
            "practice_title": p.title,
            "practice_color": p.color,
            "completed": s.completed
        })

    return render_template("history.html", history=history)

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