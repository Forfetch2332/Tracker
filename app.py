import json
from datetime import date, datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user
)

from models import db, User, Practice, PracticeEntry, init_practices


app = Flask(__name__)
app.config["SECRET_KEY"] = "super-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tracker_demo.sqlite"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()
    init_practices()


# -----------------------------
# Flask-Login
# -----------------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login_page"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# -----------------------------
# Маршруты
# -----------------------------
@app.route("/")
def welcome_page():
    return render_template(
        "welcome.html",
        login=url_for("login_page"),
        register=url_for("register_page"),
        today=url_for("today_page"),
        practices=url_for("practice_list_page")
    )


@app.route("/register", methods=["GET", "POST"])
def register_page():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if User.query.filter_by(username=username).first():
            flash("Пользователь уже существует", "danger")
            return redirect(url_for("register_page"))

        user = User(username=username)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash("Аккаунт создан", "success")
        return redirect(url_for("login_page"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash("Неверный логин или пароль", "danger")
            return redirect(url_for("login_page"))

        login_user(user)
        return redirect(url_for("today_page"))

    return render_template("login.html")


@app.route("/logout")
def logout_page():
    logout_user()
    return redirect(url_for("welcome_page"))


@app.route("/today")
@login_required
def today_page():
    practices = Practice.query.all()
    return render_template("today.html", practices=practices)


@app.route("/guide")
@login_required
def guide_page():
    practices = Practice.query.all()
    return render_template("guide.html", practices=practices)

@app.route("/practices")
@login_required
def practice_list_page():
    practices = Practice.query.all()
    return render_template("practice_list.html", practices=practices)

@app.route("/practice/<int:pid>")
@login_required
def practice_info(pid):
    practice = Practice.query.get_or_404(pid)
    schema = json.loads(practice.form_schema_json)
    return render_template("practice_info.html", practice=practice, schema=schema)


@app.route("/practice/<int:pid>/form", methods=["GET", "POST"])
@login_required
def practice_form(pid):
    practice = Practice.query.get_or_404(pid)
    schema = json.loads(practice.form_schema_json)

    if request.method == "POST":
        fields = {}
        for field in schema:
            key = field["key"]
            fields[key] = request.form.get(key)

        entry = PracticeEntry(
            practice_id=pid,
            entry_date=str(date.today()),
            fields_json=json.dumps(fields, ensure_ascii=False)
        )

        db.session.add(entry)
        db.session.commit()

        flash("Практика сохранена", "success")
        return redirect(url_for("practice_detail", pid=pid))

    return render_template("practice_form.html", practice=practice, schema=schema)


@app.route("/practice/<int:pid>/detail")
@login_required
def practice_detail(pid):
    practice = Practice.query.get_or_404(pid)
    entries = PracticeEntry.query.filter_by(practice_id=pid).all()
    schema = json.loads(practice.form_schema_json)
    return render_template("practice_detail.html", practice=practice, entries=entries, schema=schema)


@app.route("/progress")
@login_required
def progress_page():
    total_entries = PracticeEntry.query.count()
    unique_practices = PracticeEntry.query.with_entities(PracticeEntry.practice_id).distinct().count()

    # streak (серия дней подряд)
    dates = [e.entry_date for e in PracticeEntry.query.all()]
    streak = calculate_streak(dates)

    return render_template(
        "progress.html",
        total_entries=total_entries,
        unique_practices=unique_practices,
        streak=streak
    )
def calculate_streak(dates):
    if not dates:
        return 0

    dates = sorted(set(dates), reverse=True)
    streak = 1

    from datetime import datetime, timedelta
    today = datetime.today().date()

    if datetime.strptime(dates[0], "%Y-%m-%d").date() != today:
        return 0

    for i in range(1, len(dates)):
        prev = datetime.strptime(dates[i - 1], "%Y-%m-%d").date()
        curr = datetime.strptime(dates[i], "%Y-%m-%d").date()

        if prev - curr == timedelta(days=1):
            streak += 1
        else:
            break

    return streak


@app.context_processor
def inject_year():
    return {"current_year": datetime.now().year}

@app.route("/charts")
@login_required
def charts_page():
    return render_template("charts.html")


if __name__ == "__main__":
    app.run(debug=True)
