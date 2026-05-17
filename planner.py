"""
routes/planner.py
-----------------
Endpoints:
  POST /api/planner/generate   — generate a smart study plan
  GET  /api/planner/plans      — list saved plans
  GET  /api/planner/plans/<id> — get one plan

AI Logic (rule-based):
  - Distributes subjects by difficulty weighting
  - Adds revision days near exam date
  - Embeds short breaks into every session
  - Flags weak (Hard) subjects for extra slots
"""

from flask import Blueprint, request, jsonify
from database import get_db
from models import get_user_from_token
from datetime import datetime, timedelta
import json

planner_bp = Blueprint("planner", __name__)


def auth_required():
    token = (request.headers.get("Authorization", "") or "").replace("Bearer ", "")
    user  = get_user_from_token(token)
    if not user:
        return None, (jsonify({"error": "Unauthorized"}), 401)
    return user, None


# ── Weights per difficulty ─────────────────────────────────────────────────────
DIFFICULTY_WEIGHT = {"Hard": 3, "Medium": 2, "Easy": 1}
TIME_BLOCKS = [                         # possible start times for slots
    "07:00", "08:00", "09:00", "10:00", "11:00",
    "13:00", "14:00", "15:00", "16:00", "17:00",
    "19:00", "20:00",
]


def _build_day_schedule(subjects_weighted: list[dict], daily_hours: float, date_str: str) -> dict:
    """
    Build a single day's timetable.
    subjects_weighted: [{"name":..., "weight":..., "difficulty":...}, ...]
    Returns a day dict with a list of time blocks.
    """
    total_weight = sum(s["weight"] for s in subjects_weighted)
    slots = []
    ptr   = 0                           # pointer into TIME_BLOCKS

    for subj in subjects_weighted:
        # Time proportion for this subject on this day
        frac  = subj["weight"] / total_weight if total_weight else 0
        hours = round(frac * daily_hours, 1)
        if hours < 0.5:
            hours = 0.5                 # minimum 30 min per subject

        # Build slot
        if ptr < len(TIME_BLOCKS):
            start = TIME_BLOCKS[ptr]
            # Calculate end time
            sh, sm = map(int, start.split(":"))
            total_minutes = int(hours * 60)
            end_minutes   = sh * 60 + sm + total_minutes
            end = f"{end_minutes // 60:02d}:{end_minutes % 60:02d}"

            slots.append({
                "type":        "study",
                "subject":     subj["name"],
                "difficulty":  subj["difficulty"],
                "start":       start,
                "end":         end,
                "duration_hr": hours,
                "tip":         _get_tip(subj["difficulty"])
            })
            ptr += 1

            # Add a break after every study block
            break_start = end
            bsh, bsm    = end_minutes // 60, end_minutes % 60
            bend_min    = bsh * 60 + bsm + 15
            break_end   = f"{bend_min // 60:02d}:{bend_min % 60:02d}"
            slots.append({
                "type":    "break",
                "subject": "Break",
                "start":   break_start,
                "end":     break_end
            })
            ptr += 1

    return {"date": date_str, "slots": slots}


def _build_revision_day(subjects: list[str], date_str: str) -> dict:
    """Build a light revision day near the exam."""
    slots = []
    for i, subj in enumerate(subjects):
        ptr   = i * 2
        start = TIME_BLOCKS[ptr] if ptr < len(TIME_BLOCKS) else "09:00"
        slots.append({
            "type":    "revision",
            "subject": subj,
            "start":   start,
            "end":     "...",
            "tip":     "Quick recall — re-read notes, solve 5 MCQs"
        })
    return {"date": date_str, "slots": slots, "label": "📝 Revision Day"}


def _get_tip(difficulty: str) -> str:
    tips = {
        "Hard":   "Focus deeply. Avoid distractions. Take notes.",
        "Medium": "Practice problems after reading theory.",
        "Easy":   "Skim and revise. Move faster today."
    }
    return tips.get(difficulty, "Stay focused!")


def _ai_suggestions(subjects_weighted: list[dict], days_left: int) -> list[str]:
    """Rule-based AI suggestions."""
    suggestions = []
    hard_subjects = [s["name"] for s in subjects_weighted if s["difficulty"] == "Hard"]
    easy_subjects = [s["name"] for s in subjects_weighted if s["difficulty"] == "Easy"]

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
        suggestions.append("🔴 Less than a week to exam! Switch to full revision mode. No new topics.")
    elif days_left <= 14:
        suggestions.append("🟡 Two weeks left. Focus on completing all topics and start daily revision.")
    else:
        suggestions.append("🟢 Good time buffer. Cover new topics first, then revise.")
    return suggestions


# ── POST /generate ─────────────────────────────────────────────────────────────
@planner_bp.route("/generate", methods=["POST"])
def generate_plan():
    user, err = auth_required()
    if err: return err

    data        = request.get_json()
    exam_date   = data.get("exam_date", "")          # YYYY-MM-DD
    daily_hours = float(data.get("daily_hours", 4))  # hours per day
    subjects_in = data.get("subjects", [])            # [{name, difficulty}]

    # ── Validate ──────────────────────────────────────────────────────────────
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

    today     = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    days_left = (exam_dt - today).days

    if days_left <= 0:
        return jsonify({"error": "Exam date must be in the future"}), 400

    # ── Build weighted subject list ───────────────────────────────────────────
    subjects_weighted = []
    for s in subjects_in:
        diff   = s.get("difficulty", "Medium")
        weight = DIFFICULTY_WEIGHT.get(diff, 2)
        subjects_weighted.append({
            "name":       s.get("name", "Unknown").strip(),
            "difficulty": diff,
            "weight":     weight
        })

    # ── Generate day-by-day plan ──────────────────────────────────────────────
    plan_days  = []
    # Reserve last 2 days (or 1 if only 2 days left) for revision
    revision_days = min(2, max(1, days_left // 5))
    study_days    = days_left - revision_days

    subject_names = [s["name"] for s in subjects_weighted]

    for i in range(study_days):
        day_dt  = today + timedelta(days=i)
        day_str = day_dt.strftime("%Y-%m-%d")
        label   = day_dt.strftime("%A, %d %b %Y")

        day = _build_day_schedule(subjects_weighted, daily_hours, day_str)
        day["label"] = label
        plan_days.append(day)

    # Revision days at the end
    for j in range(revision_days):
        day_dt  = today + timedelta(days=study_days + j)
        day_str = day_dt.strftime("%Y-%m-%d")
        rev     = _build_revision_day(subject_names, day_str)
        rev["label"] = day_dt.strftime("%A, %d %b %Y") + " (Revision)"
        plan_days.append(rev)

    # ── Compile result ────────────────────────────────────────────────────────
    plan = {
        "exam_date":       exam_date,
        "days_left":       days_left,
        "daily_hours":     daily_hours,
        "total_study_days": study_days,
        "revision_days":   revision_days,
        "subjects":        subjects_weighted,
        "days":            plan_days,
        "ai_suggestions":  _ai_suggestions(subjects_weighted, days_left)
    }

    # ── Save to DB ────────────────────────────────────────────────────────────
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO study_plans (user_id, exam_date, daily_hours, plan_json) VALUES (?, ?, ?, ?)",
        (user["id"], exam_date, daily_hours, json.dumps(plan))
    )
    plan_id = cursor.lastrowid
    conn.commit()
    conn.close()

    plan["plan_id"] = plan_id
    return jsonify({"plan": plan}), 201


# ── GET /plans ─────────────────────────────────────────────────────────────────
@planner_bp.route("/plans", methods=["GET"])
def list_plans():
    user, err = auth_required()
    if err: return err

    conn  = get_db()
    rows  = conn.execute(
        "SELECT id, exam_date, daily_hours, created_at FROM study_plans WHERE user_id = ? ORDER BY id DESC LIMIT 10",
        (user["id"],)
    ).fetchall()
    conn.close()
    return jsonify({"plans": [dict(r) for r in rows]})


# ── GET /plans/<id> ────────────────────────────────────────────────────────────
@planner_bp.route("/plans/<int:plan_id>", methods=["GET"])
def get_plan(plan_id):
    user, err = auth_required()
    if err: return err

    conn = get_db()
    row  = conn.execute(
        "SELECT * FROM study_plans WHERE id = ? AND user_id = ?",
        (plan_id, user["id"])
    ).fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Plan not found"}), 404

    plan = json.loads(row["plan_json"])
    plan["plan_id"] = row["id"]
    return jsonify({"plan": plan})
