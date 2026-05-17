"""
routes/progress.py
------------------
Endpoints:
  GET  /api/progress/           — weekly summary + subject stats
  POST /api/progress/           — log study hours for a subject
  GET  /api/progress/streak     — study streak (consecutive days)
  GET  /api/progress/suggestions— AI-generated improvement suggestions
"""

from flask import Blueprint, request, jsonify
from database import get_db
from models import get_user_from_token
from datetime import date, timedelta, datetime

progress_bp = Blueprint("progress", __name__)


def auth_required():
    token = (request.headers.get("Authorization", "") or "").replace("Bearer ", "")
    user  = get_user_from_token(token)
    if not user:
        return None, (jsonify({"error": "Unauthorized"}), 401)
    return user, None


# ── Log study session ──────────────────────────────────────────────────────────
@progress_bp.route("/", methods=["POST"])
def log_progress():
    user, err = auth_required()
    if err: return err

    data          = request.get_json()
    subject       = (data.get("subject") or "").strip()
    hours_studied = float(data.get("hours_studied", 0))
    log_date      = data.get("date") or str(date.today())

    if not subject:
        return jsonify({"error": "subject required"}), 400
    if hours_studied <= 0:
        return jsonify({"error": "hours_studied must be > 0"}), 400

    conn = get_db()
    # If entry exists for this user/subject/date, accumulate hours
    existing = conn.execute(
        "SELECT id, hours_studied FROM progress WHERE user_id=? AND subject=? AND date=?",
        (user["id"], subject, log_date)
    ).fetchone()

    if existing:
        new_hours = existing["hours_studied"] + hours_studied
        conn.execute(
            "UPDATE progress SET hours_studied=? WHERE id=?",
            (new_hours, existing["id"])
        )
    else:
        conn.execute(
            "INSERT INTO progress (user_id, subject, hours_studied, date) VALUES (?,?,?,?)",
            (user["id"], subject, hours_studied, log_date)
        )

    conn.commit()
    conn.close()
    return jsonify({"message": "Progress logged", "subject": subject, "hours": hours_studied}), 201


# ── Get summary ────────────────────────────────────────────────────────────────
@progress_bp.route("/", methods=["GET"])
def get_summary():
    user, err = auth_required()
    if err: return err

    conn = get_db()

    # Last 7 days daily totals
    weekly = []
    for i in range(6, -1, -1):
        day     = date.today() - timedelta(days=i)
        day_str = str(day)
        row = conn.execute(
            "SELECT COALESCE(SUM(hours_studied), 0) as total FROM progress WHERE user_id=? AND date=?",
            (user["id"], day_str)
        ).fetchone()
        weekly.append({
            "date":  day_str,
            "label": day.strftime("%a"),
            "hours": round(row["total"], 1)
        })

    # Subject-wise totals (all time)
    subj_rows = conn.execute("""
        SELECT subject,
               ROUND(SUM(hours_studied), 1) AS total_hours,
               COUNT(DISTINCT date)         AS days_studied
        FROM progress
        WHERE user_id = ?
        GROUP BY subject
        ORDER BY total_hours DESC
    """, (user["id"],)).fetchall()

    # Total hours today
    today_row = conn.execute(
        "SELECT COALESCE(SUM(hours_studied),0) as t FROM progress WHERE user_id=? AND date=?",
        (user["id"], str(date.today()))
    ).fetchone()

    # Topic completion stats
    topic_stats = conn.execute("""
        SELECT s.subject_name,
               COUNT(t.id)                             AS total_topics,
               SUM(CASE WHEN t.completed=1 THEN 1 ELSE 0 END) AS done_topics
        FROM subjects s
        LEFT JOIN topics t ON t.subject_id = s.id
        WHERE s.user_id = ?
        GROUP BY s.id
    """, (user["id"],)).fetchall()

    conn.close()

    subject_summary = []
    for r in subj_rows:
        subject_summary.append({
            "subject":      r["subject"],
            "total_hours":  r["total_hours"],
            "days_studied": r["days_studied"]
        })

    topic_summary = []
    for r in topic_stats:
        total = r["total_topics"] or 0
        done  = r["done_topics"]  or 0
        pct   = round((done / total * 100) if total else 0, 1)
        topic_summary.append({
            "subject":        r["subject_name"],
            "total_topics":   total,
            "done_topics":    done,
            "completion_pct": pct
        })

    return jsonify({
        "weekly":          weekly,
        "subject_summary": subject_summary,
        "topic_summary":   topic_summary,
        "hours_today":     round(today_row["t"], 1)
    })


# ── Study streak ───────────────────────────────────────────────────────────────
@progress_bp.route("/streak", methods=["GET"])
def get_streak():
    user, err = auth_required()
    if err: return err

    conn = get_db()
    # Get all distinct dates with study activity, newest first
    rows = conn.execute(
        "SELECT DISTINCT date FROM progress WHERE user_id=? ORDER BY date DESC",
        (user["id"],)
    ).fetchall()
    conn.close()

    dates = [r["date"] for r in rows]
    if not dates:
        return jsonify({"streak": 0, "days": []})

    streak     = 0
    check_date = date.today()

    for d_str in dates:
        d = datetime.strptime(d_str, "%Y-%m-%d").date()
        if d == check_date or d == check_date - timedelta(days=1):
            streak    += 1
            check_date = d - timedelta(days=1)
        else:
            break

    return jsonify({"streak": streak, "dates": dates[:30]})


# ── AI suggestions ─────────────────────────────────────────────────────────────
@progress_bp.route("/suggestions", methods=["GET"])
def get_suggestions():
    user, err = auth_required()
    if err: return err

    conn = get_db()

    # Find subjects with fewest hours relative to others
    subj_hours = conn.execute("""
        SELECT subject, COALESCE(SUM(hours_studied), 0) AS hrs
        FROM progress WHERE user_id=?
        GROUP BY subject ORDER BY hrs ASC
    """, (user["id"],)).fetchall()

    # Find Hard topics not yet completed
    hard_pending = conn.execute("""
        SELECT t.topic_name, s.subject_name
        FROM topics t
        JOIN subjects s ON s.id = t.subject_id
        WHERE s.user_id=? AND t.difficulty='Hard' AND t.completed=0
        LIMIT 5
    """, (user["id"],)).fetchall()

    # Upcoming exams within 14 days
    urgent_exams = conn.execute("""
        SELECT subject, exam_date FROM exams
        WHERE user_id=?
          AND exam_date BETWEEN date('now') AND date('now', '+14 days')
        ORDER BY exam_date ASC
    """, (user["id"],)).fetchall()

    conn.close()

    suggestions = []

    if subj_hours:
        weakest = subj_hours[0]["subject"]
        suggestions.append({
            "type":    "weak_subject",
            "icon":    "⚠️",
            "title":   f"Focus on {weakest}",
            "message": f"'{weakest}' has the least study time. "
                       "Add 1-2 extra sessions this week."
        })

    for hp in hard_pending[:3]:
        suggestions.append({
            "type":    "hard_topic",
            "icon":    "🔴",
            "title":   f"Pending: {hp['topic_name']}",
            "message": f"Hard topic in {hp['subject_name']} still pending. "
                       "Block 90 minutes for this today."
        })

    for ue in urgent_exams:
        suggestions.append({
            "type":    "exam_alert",
            "icon":    "📅",
            "title":   f"Exam Alert: {ue['subject']}",
            "message": f"{ue['subject']} exam on {ue['exam_date']}. "
                       "Switch to revision-only mode for this subject."
        })

    if not suggestions:
        suggestions.append({
            "type":    "positive",
            "icon":    "🎉",
            "title":   "Great Progress!",
            "message": "You're on track. Keep maintaining your daily study habit."
        })

    return jsonify({"suggestions": suggestions})
