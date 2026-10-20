"""Examination tracking endpoints.

Authenticated users can list upcoming exams and add or remove exam dates.
"""

from datetime import date, datetime

from flask import Blueprint, jsonify, request

from database import get_db
from models import get_user_from_token

exams_bp = Blueprint("exams", __name__)


def auth_required():
    """Return the current user or a 401 response when authentication fails."""
    token = (request.headers.get("Authorization", "") or "").replace("Bearer ", "")
    user = get_user_from_token(token)
    if not user:
        return None, (jsonify({"error": "Unauthorized"}), 401)
    return user, None


def _days_left(exam_date_str: str) -> int:
    """Return the number of days remaining until an exam date."""
    try:
        exam_date = datetime.strptime(exam_date_str, "%Y-%m-%d").date()
        return (exam_date - date.today()).days
    except Exception:
        return -1


@exams_bp.route("/", methods=["GET"])
def list_exams():
    """List exams for the current user, sorted by date."""
    user, err = auth_required()
    if err:
        return err

    conn = get_db()
    exams = conn.execute(
        "SELECT * FROM exams WHERE user_id = ? ORDER BY exam_date ASC",
        (user["id"],),
    ).fetchall()
    conn.close()

    results = []
    for exam in exams:
        row = dict(exam)
        row["days_left"] = _days_left(exam["exam_date"])
        results.append(row)

    return jsonify({"exams": results})


@exams_bp.route("/", methods=["POST"])
def add_exam():
    """Add an exam date for the current user."""
    user, err = auth_required()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    subject = (data.get("subject") or "").strip()
    exam_date = (data.get("exam_date") or "").strip()
    notes = (data.get("notes") or "").strip()

    if not subject or not exam_date:
        return jsonify({"error": "subject and exam_date required"}), 400

    try:
        datetime.strptime(exam_date, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Invalid date. Use YYYY-MM-DD"}), 400

    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO exams (user_id, subject, exam_date, notes) VALUES (?, ?, ?, ?)",
        (user["id"], subject, exam_date, notes),
    )
    conn.commit()
    exam_id = cursor.lastrowid
    conn.close()

    return (
        jsonify(
            {
                "message": "Exam added",
                "id": exam_id,
                "subject": subject,
                "exam_date": exam_date,
                "days_left": _days_left(exam_date),
            }
        ),
        201,
    )


@exams_bp.route("/<int:exam_id>", methods=["DELETE"])
def delete_exam(exam_id):
    """Delete an exam record for the authenticated user."""
    user, err = auth_required()
    if err:
        return err

    conn = get_db()
    conn.execute(
        "DELETE FROM exams WHERE id = ? AND user_id = ?", (exam_id, user["id"])
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Exam deleted"})
