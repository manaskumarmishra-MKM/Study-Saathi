"""Planner routes for generating smart study schedules.

The planner builds a rule-based, day-by-day timetable using subject difficulty,
exam dates, and a short revision window near the exam.
"""

import json
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

from database import get_db
from models import get_user_from_token

planner_bp = Blueprint("planner", __name__)

DIFFICULTY_WEIGHT = {"Hard": 3, "Medium": 2, "Easy": 1}
TIME_BLOCKS = [
    "07:00", "08:00", "09:00", "10:00", "11:00",
    "13:00", "14:00", "15:00", "16:00", "17:00",
    "19:00", "20:00",
]


def auth_required():
    """Return the current user or a 401 response if the token is invalid."""
    token = (request.headers.get("Authorization", "") or "").replace("Bearer ", "")
    user = get_user_from_token(token)
    if not user:
        return None, (jsonify({"error": "Unauthorized"}), 401)
    return user, None


def _get_tip(difficulty: str) -> str:
    """Return a small study tip based on the subject difficulty."""
    tips = {
        "Hard": "Focus deeply. Avoid distractions and take notes.",
        "Medium": "Practice problems after reading the theory.",
        "Easy": "Skim and revise quickly to keep momentum.",
    }
    return tips.get(difficulty, "Stay focused and keep moving.")


def _build_day_schedule(subjects_weighted: list[dict], daily_hours: float, date_str: str) -> dict:
    """Build one day of a study plan with subject blocks and short breaks."""
    total_weight = sum(subject["weight"] for subject in subjects_weighted)
    slots = []
    pointer = 0

    for subject in subjects_weighted:
        fraction = subject["weight"] / total_weight if total_weight else 0
        duration_hours = round(fraction * daily_hours, 1)
        if duration_hours < 0.5:
            duration_hours = 0.5

        if pointer >= len(TIME_BLOCKS):
            continue

        start = TIME_BLOCKS[pointer]
        start_hour, start_minute = map(int, start.split(":"))
        total_minutes = int(duration_hours * 60)
        end_minutes = start_hour * 60 + start_minute + total_minutes
        end = f"{end_minutes // 60:02d}:{end_minutes % 60:02d}"

        slots.append(
            {
                "type": "study",
                "subject": subject["name"],
                "difficulty": subject["difficulty"],
                "start": start,
                "end": end,
                "duration_hr": duration_hours,
                "tip": _get_tip(subject["difficulty"]),
            }
        )
        pointer += 1

        break_start = end
        break_hour, break_minute = divmod(end_minutes, 60)
        break_end_minute = break_hour * 60 + break_minute + 15
        break_end = f"{break_end_minute // 60:02d}:{break_end_minute % 60:02d}"
        slots.append({
            "type": "break",
            "subject": "Break",
            "start": break_start,
            "end": break_end,
        })
        pointer += 1

    return {"date": date_str, "slots": slots}


def _build_revision_day(subjects: list[str], date_str: str) -> dict:
    """Build a light revision day close to the exam."""
    slots = []
    for index, subject in enumerate(subjects):
        start_index = index * 2
        start_time = TIME_BLOCKS[start_index] if start_index < len(TIME_BLOCKS) else "09:00"
        slots.append(
            {
                "type": "revision",
                "subject": subject,
                "start": start_time,
                "end": "...",
                "tip": "Quick recall — revisit notes and solve 5 MCQs.",
            }
        )
    return {"date": date_str, "slots": slots, "label": "📝 Revision Day"}


def _ai_suggestions(subjects_weighted: list[dict], days_left: int) -> list[str]:
    """Generate rule-based suggestions to guide study priorities."""
    suggestions = []
    hard_subjects = [subject["name"] for subject in subjects_weighted if subject["difficulty"] == "Hard"]
    easy_subjects = [subject["name"] for subject in subjects_weighted if subject["difficulty"] == "Easy"]

    if hard_subjects:
        suggestions.append(
            f"⚠ Spend extra time on hard subjects: {', '.join(hard_subjects)}. "
            "Schedule them in your morning peak hours."
        )
    if easy_subjects:
        suggestions.append(
            f"✅ {', '.join(easy_subjects)} look manageable. "
            "Use lighter revision slots for these."
        )
    if days_left <= 7:
        suggestions.append("🔴 Less than a week left. Focus purely on recall and revision.")
    elif days_left <= 14:
        suggestions.append("🟡 Two weeks left. Complete all topics and begin daily revision.")
    else:
        suggestions.append("🟢 You have enough buffer. Cover new topics first, then revise.")

    return suggestions


@planner_bp.route("/generate", methods=["POST"])
def generate_plan():
    """Generate a study plan and save it for the authenticated user."""
    user, err = auth_required()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    exam_date = (data.get("exam_date") or "").strip()
    daily_hours = float(data.get("daily_hours", 4))
    subjects_in = data.get("subjects", [])

    if not exam_date:
        return jsonify({"error": "exam_date required (YYYY-MM-DD)"}), 400
    if not subjects_in:
        return jsonify({"error": "At least one subject required"}), 400
    if daily_hours < 1 or daily_hours > 16:
        daily_hours = 4

    try:
        exam_dt = datetime.strptime(exam_date, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    days_left = (exam_dt - today).days
    if days_left <= 0:
        return jsonify({"error": "Exam date must be in the future"}), 400

    subjects_weighted = []
    for subject in subjects_in:
        diff = subject.get("difficulty", "Medium")
        weight = DIFFICULTY_WEIGHT.get(diff, 2)
        subjects_weighted.append(
            {
                "name": subject.get("name", "Unknown").strip(),
                "difficulty": diff,
                "weight": weight,
            }
        )

    plan_days = []
    revision_days = min(2, max(1, days_left // 5))
    study_days = days_left - revision_days
    subject_names = [subject["name"] for subject in subjects_weighted]

    for offset in range(study_days):
        day_dt = today + timedelta(days=offset)
        day_str = day_dt.strftime("%Y-%m-%d")
        day = _build_day_schedule(subjects_weighted, daily_hours, day_str)
        day["label"] = day_dt.strftime("%A, %d %b %Y")
        plan_days.append(day)

    for offset in range(revision_days):
        day_dt = today + timedelta(days=study_days + offset)
        day_str = day_dt.strftime("%Y-%m-%d")
        revision_day = _build_revision_day(subject_names, day_str)
        revision_day["label"] = day_dt.strftime("%A, %d %b %Y") + " (Revision)"
        plan_days.append(revision_day)

    plan = {
        "exam_date": exam_date,
        "days_left": days_left,
        "daily_hours": daily_hours,
        "total_study_days": study_days,
        "revision_days": revision_days,
        "subjects": subjects_weighted,
        "days": plan_days,
        "ai_suggestions": _ai_suggestions(subjects_weighted, days_left),
    }

    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO study_plans (user_id, exam_date, daily_hours, plan_json) VALUES (?, ?, ?, ?)",
        (user["id"], exam_date, daily_hours, json.dumps(plan)),
    )
    plan_id = cursor.lastrowid
    conn.commit()
    conn.close()

    plan["plan_id"] = plan_id
    return jsonify({"plan": plan}), 201


@planner_bp.route("/plans", methods=["GET"])
def list_plans():
    """List the recently saved study plans for the authenticated user."""
    user, err = auth_required()
    if err:
        return err

    conn = get_db()
    rows = conn.execute(
        "SELECT id, exam_date, daily_hours, created_at FROM study_plans WHERE user_id = ? ORDER BY id DESC LIMIT 10",
        (user["id"],),
    ).fetchall()
    conn.close()
    return jsonify({"plans": [dict(row) for row in rows]})


@planner_bp.route("/plans/<int:plan_id>", methods=["GET"])
def get_plan(plan_id):
    """Fetch one saved plan by id."""
    user, err = auth_required()
    if err:
        return err

    conn = get_db()
    row = conn.execute(
        "SELECT * FROM study_plans WHERE id = ? AND user_id = ?",
        (plan_id, user["id"]),
    ).fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Plan not found"}), 404

    plan = json.loads(row["plan_json"])
    plan["plan_id"] = row["id"]
    return jsonify({"plan": plan})
