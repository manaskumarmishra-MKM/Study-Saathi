"""Progress tracking endpoints.

This module stores study hours, calculates study streaks, and surfaces simple AI-like
improvement suggestions based on weak subjects and upcoming exams.
"""

from datetime import date, datetime, timedelta

from flask import Blueprint, jsonify, request

from database import get_db
from models import get_user_from_token

progress_bp = Blueprint("progress", __name__)


def auth_required():
    """Return the current user or a 401 error response."""
    token = (request.headers.get("Authorization", "") or "").replace("Bearer ", "")
    user = get_user_from_token(token)
    if not user:
        return None, (jsonify({"error": "Unauthorized"}), 401)
    return user, None


@progress_bp.route("/", methods=["POST"])
def log_progress():
    """Log study hours for a subject on a given date."""
    user, err = auth_required()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    subject = (data.get("subject") or "").strip()
    hours_studied = float(data.get("hours_studied", 0))
    log_date = data.get("date") or str(date.today())

    if not subject:
        return jsonify({"error": "subject required"}), 400
    if hours_studied <= 0:
        return jsonify({"error": "hours_studied must be > 0"}), 400

    conn = get_db()
    existing = conn.execute(
        "SELECT id, hours_studied FROM progress WHERE user_id=? AND subject=? AND date=?",
        (user["id"], subject, log_date),
    ).fetchone()

    if existing:
        updated_hours = existing["hours_studied"] + hours_studied
        conn.execute(
            "UPDATE progress SET hours_studied=? WHERE id=?",
            (updated_hours, existing["id"]),
        )
    else:
        conn.execute(
            "INSERT INTO progress (user_id, subject, hours_studied, date) VALUES (?,?,?,?)",
            (user["id"], subject, hours_studied, log_date),
        )

    conn.commit()
    conn.close()
    return jsonify({"message": "Progress logged", "subject": subject, "hours": hours_studied}), 201


@progress_bp.route("/", methods=["GET"])
def get_summary():
    """Return weekly totals, per-subject totals, and topic completion stats."""
    user, err = auth_required()
    if err:
        return err

    conn = get_db()

    weekly = []
    for offset in range(6, -1, -1):
        day = date.today() - timedelta(days=offset)
        day_str = str(day)
        row = conn.execute(
            "SELECT COALESCE(SUM(hours_studied), 0) as total FROM progress WHERE user_id=? AND date=?",
            (user["id"], day_str),
        ).fetchone()
        weekly.append({"date": day_str, "label": day.strftime("%a"), "hours": round(row["total"], 1)})

    subject_rows = conn.execute(
        """
        SELECT subject,
               ROUND(SUM(hours_studied), 1) AS total_hours,
               COUNT(DISTINCT date) AS days_studied
        FROM progress
        WHERE user_id = ?
        GROUP BY subject
        ORDER BY total_hours DESC
        """,
        (user["id"],),
    ).fetchall()

    today_row = conn.execute(
        "SELECT COALESCE(SUM(hours_studied),0) as t FROM progress WHERE user_id=? AND date=?",
        (user["id"], str(date.today())),
    ).fetchone()

    topic_stats = conn.execute(
        """
        SELECT s.subject_name,
               COUNT(t.id) AS total_topics,
               SUM(CASE WHEN t.completed=1 THEN 1 ELSE 0 END) AS done_topics
        FROM subjects s
        LEFT JOIN topics t ON t.subject_id = s.id
        WHERE s.user_id = ?
        GROUP BY s.id
        """,
        (user["id"],),
    ).fetchall()

    conn.close()

    subject_summary = [
        {
            "subject": row["subject"],
            "total_hours": row["total_hours"],
            "days_studied": row["days_studied"],
        }
        for row in subject_rows
    ]

    topic_summary = []
    for row in topic_stats:
        total = row["total_topics"] or 0
        done = row["done_topics"] or 0
        percentage = round((done / total * 100) if total else 0, 1)
        topic_summary.append(
            {
                "subject": row["subject_name"],
                "total_topics": total,
                "done_topics": done,
                "completion_pct": percentage,
            }
        )

    return jsonify(
        {
            "weekly": weekly,
            "subject_summary": subject_summary,
            "topic_summary": topic_summary,
            "hours_today": round(today_row["t"], 1),
        }
    )


@progress_bp.route("/streak", methods=["GET"])
def get_streak():
    """Calculate the current consecutive study streak based on logged progress dates."""
    user, err = auth_required()
    if err:
        return err

    conn = get_db()
    rows = conn.execute(
        "SELECT DISTINCT date FROM progress WHERE user_id=? ORDER BY date DESC",
        (user["id"],),
    ).fetchall()
    conn.close()

    dates = [row["date"] for row in rows]
    if not dates:
        return jsonify({"streak": 0, "days": []})

    streak = 0
    check_date = date.today()
    for day_str in dates:
        day = datetime.strptime(day_str, "%Y-%m-%d").date()
        if day == check_date or day == check_date - timedelta(days=1):
            streak += 1
            check_date = day - timedelta(days=1)
        else:
            break

    return jsonify({"streak": streak, "dates": dates[:30]})


@progress_bp.route("/suggestions", methods=["GET"])
def get_suggestions():
    """Return helpful suggestions based on weak subject areas and upcoming exams."""
    user, err = auth_required()
    if err:
        return err

    conn = get_db()
    subject_hours = conn.execute(
        """
        SELECT subject, COALESCE(SUM(hours_studied), 0) AS hrs
        FROM progress
        WHERE user_id=?
        GROUP BY subject
        ORDER BY hrs ASC
        """,
        (user["id"],),
    ).fetchall()

    hard_pending = conn.execute(
        """
        SELECT t.topic_name, s.subject_name
        FROM topics t
        JOIN subjects s ON s.id = t.subject_id
        WHERE s.user_id=? AND t.difficulty='Hard' AND t.completed=0
        LIMIT 5
        """,
        (user["id"],),
    ).fetchall()

    urgent_exams = conn.execute(
        """
        SELECT subject, exam_date
        FROM exams
        WHERE user_id=?
          AND exam_date BETWEEN date('now') AND date('now', '+14 days')
        ORDER BY exam_date ASC
        """,
        (user["id"],),
    ).fetchall()
    conn.close()

    suggestions = []
    if subject_hours:
        weakest = subject_hours[0]["subject"]
        suggestions.append({
            "type": "weak_subject",
            "icon": "⚠️",
            "message": f"Your weakest subject is {weakest}. Consider adding a focused revision block this week.",
        })

    if hard_pending:
        pending = hard_pending[0]
        suggestions.append({
            "type": "hard_topic",
            "icon": "📘",
            "message": f"Priority topic: {pending['topic_name']} in {pending['subject_name']}. Aim to finish it before your next study session.",
        })

    if urgent_exams:
        next_exam = urgent_exams[0]
        suggestions.append({
            "type": "exam_focus",
            "icon": "🎯",
            "message": f"Upcoming exam: {next_exam['subject']} on {next_exam['exam_date']}. Increase revision time for this subject.",
        })

    return jsonify({"suggestions": suggestions})
