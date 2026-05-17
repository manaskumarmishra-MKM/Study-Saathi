"""
routes/subjects.py
------------------
Endpoints:
  GET    /api/subjects/             — list user's subjects + topics
  POST   /api/subjects/             — add a subject
  DELETE /api/subjects/<id>         — delete a subject
  POST   /api/subjects/<id>/topics  — add a topic to a subject
  PATCH  /api/subjects/topics/<id>  — mark topic complete/pending
  DELETE /api/subjects/topics/<id>  — delete a topic
"""

from flask import Blueprint, request, jsonify
from database import get_db
from models import get_user_from_token

subjects_bp = Blueprint("subjects", __name__)


def auth_required():
    """Helper: returns (user_dict, None) or (None, error_response)."""
    token = (request.headers.get("Authorization", "") or "").replace("Bearer ", "")
    user  = get_user_from_token(token)
    if not user:
        return None, (jsonify({"error": "Unauthorized"}), 401)
    return user, None


# ── List subjects + their topics ──────────────────────────────────────────────
@subjects_bp.route("/", methods=["GET"])
def list_subjects():
    user, err = auth_required()
    if err: return err

    conn = get_db()
    subjects = conn.execute(
        "SELECT * FROM subjects WHERE user_id = ? ORDER BY id", (user["id"],)
    ).fetchall()

    result = []
    for s in subjects:
        topics = conn.execute(
            "SELECT * FROM topics WHERE subject_id = ? ORDER BY id", (s["id"],)
        ).fetchall()
        result.append({
            **dict(s),
            "topics": [dict(t) for t in topics]
        })

    conn.close()
    return jsonify({"subjects": result})


# ── Add subject ───────────────────────────────────────────────────────────────
@subjects_bp.route("/", methods=["POST"])
def add_subject():
    user, err = auth_required()
    if err: return err

    data = request.get_json()
    name = (data.get("subject_name") or "").strip()
    if not name:
        return jsonify({"error": "subject_name is required"}), 400

    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO subjects (user_id, subject_name) VALUES (?, ?)",
        (user["id"], name)
    )
    conn.commit()
    subject_id = cursor.lastrowid
    conn.close()

    return jsonify({"message": "Subject added", "id": subject_id, "subject_name": name}), 201


# ── Delete subject ────────────────────────────────────────────────────────────
@subjects_bp.route("/<int:subject_id>", methods=["DELETE"])
def delete_subject(subject_id):
    user, err = auth_required()
    if err: return err

    conn = get_db()
    conn.execute(
        "DELETE FROM subjects WHERE id = ? AND user_id = ?", (subject_id, user["id"])
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Subject deleted"})


# ── Add topic to subject ──────────────────────────────────────────────────────
@subjects_bp.route("/<int:subject_id>/topics", methods=["POST"])
def add_topic(subject_id):
    user, err = auth_required()
    if err: return err

    # Verify the subject belongs to this user
    conn = get_db()
    subj = conn.execute(
        "SELECT id FROM subjects WHERE id = ? AND user_id = ?", (subject_id, user["id"])
    ).fetchone()
    if not subj:
        conn.close()
        return jsonify({"error": "Subject not found"}), 404

    data       = request.get_json()
    topic_name = (data.get("topic_name") or "").strip()
    difficulty = data.get("difficulty", "Medium")

    if not topic_name:
        conn.close()
        return jsonify({"error": "topic_name is required"}), 400

    if difficulty not in ("Easy", "Medium", "Hard"):
        difficulty = "Medium"

    cursor = conn.execute(
        "INSERT INTO topics (subject_id, topic_name, difficulty) VALUES (?, ?, ?)",
        (subject_id, topic_name, difficulty)
    )
    conn.commit()
    topic_id = cursor.lastrowid
    conn.close()

    return jsonify({
        "message":    "Topic added",
        "id":         topic_id,
        "topic_name": topic_name,
        "difficulty": difficulty
    }), 201


# ── Toggle topic complete ─────────────────────────────────────────────────────
@subjects_bp.route("/topics/<int:topic_id>", methods=["PATCH"])
def update_topic(topic_id):
    user, err = auth_required()
    if err: return err

    data      = request.get_json()
    completed = 1 if data.get("completed") else 0

    conn = get_db()
    # Confirm ownership via join
    row = conn.execute("""
        SELECT t.id FROM topics t
        JOIN subjects s ON s.id = t.subject_id
        WHERE t.id = ? AND s.user_id = ?
    """, (topic_id, user["id"])).fetchone()

    if not row:
        conn.close()
        return jsonify({"error": "Topic not found"}), 404

    conn.execute("UPDATE topics SET completed = ? WHERE id = ?", (completed, topic_id))
    conn.commit()
    conn.close()
    return jsonify({"message": "Topic updated"})


# ── Delete topic ──────────────────────────────────────────────────────────────
@subjects_bp.route("/topics/<int:topic_id>", methods=["DELETE"])
def delete_topic(topic_id):
    user, err = auth_required()
    if err: return err

    conn = get_db()
    conn.execute("""
        DELETE FROM topics WHERE id = ?
        AND subject_id IN (SELECT id FROM subjects WHERE user_id = ?)
    """, (topic_id, user["id"]))
    conn.commit()
    conn.close()
    return jsonify({"message": "Topic deleted"})
