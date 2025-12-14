from flask import Flask, render_template, request, redirect, url_for
from datetime import date, timedelta
from models import db, Practice, Entry, init_practices
import json

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tracker_demo.sqlite"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# Создаём таблицы и начальные практики
with app.app_context():
    db.create_all()
    init_practices()


# ============================
# TODAY PAGE
# ============================

@app.route("/")
@app.route("/today")
def today_page():
    today = date.today()

    practices = Practice.query.order_by(Practice.id).all()
    today_entries = Entry.query.filter_by(entry_date=today.isoformat()).all()

    done_practice_ids = {e.practice_id for e in today_entries}

    total = len(practices)
    done = len(done_practice_ids)
    percent = round((done / total) * 100, 1) if total > 0 else 0

    show_done_alert = request.args.get("done") == "1"

    return render_template(
        "today.html",
        practices=practices,
        done_practice_ids=done_practice_ids,
        total=total,
        done=done,
        percent=percent,
        show_done_alert=show_done_alert
    )


# ============================
# PRACTICE FORM (выполнение практики)
# ============================

@app.route("/practice/<int:practice_id>/form", methods=["GET", "POST"])
def practice_form(practice_id):
    practice = Practice.query.get_or_404(practice_id)

    schema = json.loads(practice.form_schema_json) if practice.form_schema_json else []

    if request.method == "POST":
        fields = {}
        for field in schema:
            key = field["key"]
            fields[key] = request.form.get(key, "")

        entry = Entry(
            practice_id=practice_id,
            entry_date=date.today().isoformat(),
            fields_json=json.dumps(fields, ensure_ascii=False)
        )
        db.session.add(entry)
        db.session.commit()

        return redirect(url_for("today_page", done=1))

    return render_template("practice_form.html", practice=practice, schema=schema)


# ============================
# PRACTICE LIST (простой список)
# ============================

@app.route("/practice_list")
def practice_list():
    practices = Practice.query.order_by(Practice.id).all()
    return render_template("practice_list.html", items=practices)


# ============================
# ANALYTICS PAGE (practice_detail)
# ============================

@app.route("/practice/<int:pid>")
def practice_detail(pid):
    practice = Practice.query.get_or_404(pid)

    filter_date_str = request.args.get("date")
    filter_date = None
    if filter_date_str:
        try:
            filter_date = date.fromisoformat(filter_date_str)
        except ValueError:
            filter_date = None

    all_entries_raw = (
        Entry.query
        .filter_by(practice_id=pid)
        .order_by(Entry.entry_date.asc())
        .all()
    )

    if not all_entries_raw:
        return render_template(
            "practice_detail.html",
            practice=practice,
            entries_by_date={},
            chart_labels=[],
            chart_values=[],
            total_done=0,
            current_streak=0,
            best_streak=0,
            heatmap=[],
            filter_date=filter_date_str,
            current_week=None,
            today=date.today().isoformat(),
            first_date=None,
            days_active=0,
            avg_per_day=0,
            percent_days=0,
        )

    entries = []
    for e in all_entries_raw:
        fields = json.loads(e.fields_json) if e.fields_json else {}
        entries.append({
            "date": e.entry_date,
            "fields": fields
        })

    from collections import defaultdict, Counter

    entries_by_date = defaultdict(list)
    for e in entries:
        entries_by_date[e["date"]].append(e)

    date_counts = Counter(date.fromisoformat(e.entry_date) for e in all_entries_raw)

    chart_labels = sorted(date_counts.keys())
    chart_values = [date_counts[d] for d in chart_labels]

    total_done = len(all_entries_raw)

    def calc_streak():
        dates_list = sorted(date.fromisoformat(e.entry_date) for e in all_entries_raw)
        dates_set = set(dates_list)

        streak = 0
        d = date.today()
        while d in dates_set:
            streak += 1
            d -= timedelta(days=1)

        best = 1
        current = 1
        for i in range(1, len(dates_list)):
            if dates_list[i] == dates_list[i - 1] + timedelta(days=1):
                current += 1
                best = max(best, current)
            else:
                current = 1

        return streak, best

    current_streak, best_streak = calc_streak()

    today = date.today()
    first_date = date.fromisoformat(all_entries_raw[0].entry_date)
    days_active = (today - first_date).days + 1

    days_with_entries = len(set(date.fromisoformat(e.entry_date) for e in all_entries_raw))
    avg_per_day = round(total_done / days_active, 2)
    percent_days = round((days_with_entries / days_active) * 100, 1)

    start_date = first_date - timedelta(days=first_date.weekday())
    end_date = today + timedelta(days=(6 - today.weekday()))

    heatmap = []
    d = start_date

    while d <= end_date:
        week_index = (d - start_date).days // 7

        heatmap.append({
            "date": d.isoformat(),
            "count": date_counts.get(d, 0),
            "weekday": d.weekday(),
            "week": week_index,
        })

        d += timedelta(days=1)

    current_week = None
    for cell in heatmap:
        if cell["date"] == today.isoformat():
            current_week = cell["week"]
            break

    return render_template(
        "practice_detail.html",
        practice=practice,
        entries_by_date=dict(entries_by_date),
        chart_labels=[d.isoformat() for d in chart_labels],
        chart_values=chart_values,
        total_done=total_done,
        current_streak=current_streak,
        best_streak=best_streak,
        heatmap=heatmap,
        filter_date=filter_date_str,
        current_week=current_week,
        today=today.isoformat(),
        first_date=first_date,
        days_active=days_active,
        avg_per_day=avg_per_day,
        percent_days=percent_days,
    )


# ============================
# STATIC PAGES
# ============================

@app.route("/progress")
def progress_page():
    return render_template("progress.html")


@app.route("/charts")
def charts_page():
    return render_template("charts.html")


@app.route("/guide")
def guide_page():
    practices = Practice.query.order_by(Practice.id).all()
    return render_template("guide.html", practices=practices)


@app.route("/practice_info/<int:pid>")
def practice_info(pid):
    practice = Practice.query.get_or_404(pid)

    schema = []
    if practice.form_schema_json:
        schema = json.loads(practice.form_schema_json)

    return render_template("practice_info.html", practice=practice, schema=schema)


if __name__ == "__main__":
    app.run(debug=True)
