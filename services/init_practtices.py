from app import db
from models import Practice, PracticeExample, PracticeTip


def init_practices():
    practices_data = [
        {
            "name": "Осознанное дыхание",
            "color": "#A7D8F0",
            "description": "Мягкий способ вернуть себя в момент и снизить внутреннее напряжение.",
            "category": "телесная",
            "difficulty": 1,
            "motivation": (
                "Эта практика — якорь. Она всегда доступна, не требует условий "
                "и даёт быстрый эффект. Чем чаще ты возвращаешься к дыханию, "
                "тем устойчивее становится твоя система."
            ),
            "examples": [
                "Сделай 3 глубоких вдоха, положив руку на грудь",
                "Заметь, что чувствуешь в теле",
                "Позволь себе выдохнуть чуть медленнее"
            ],
            "tips": [
                "Можно делать в транспорте",
                "Подходит перед сном",
                "Работает даже за 10 секунд"
            ]
        }
    ]

    for p in practices_data:
        practice = Practice.query.filter_by(name=p["name"]).first()

        if not practice:
            practice = Practice(
                name=p["name"],
                color=p["color"],
                description=p["description"],
                category=p["category"],
                difficulty=p["difficulty"],
                motivation=p["motivation"]
            )
            db.session.add(practice)
            db.session.commit()

        # Примеры
        for ex in p["examples"]:
            exists = PracticeExample.query.filter_by(
                practice_id=practice.id,
                text=ex
            ).first()
            if not exists:
                db.session.add(PracticeExample(practice_id=practice.id, text=ex))

        # Подсказки
        for tip in p["tips"]:
            exists = PracticeTip.query.filter_by(
                practice_id=practice.id,
                text=tip
            ).first()
            if not exists:
                db.session.add(PracticeTip(practice_id=practice.id, text=tip))

    db.session.commit()
