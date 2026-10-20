"""Subject and topic management endpoints.

These routes allow users to organize study subjects and mark each topic as complete
or incomplete.
"""

from flask import Blueprint, jsonify, request

from database import get_db
from models import get_user_from_token

subjects_bp = Blueprint("subjects", __name__)


def auth_required():
    """Return the current user or a 401 response if the token is missing."""
    token = (request.headers.get("Authorization", "") or "").replace("Bearer ", "")
    user = get_user_from_token(token)
    if not user:
        return None, (jsonify({"error": "Unauthorized"}), 401)
    return user, None


@subjects_bp.route("/", methods=["GET"])
def list_subjects():
    """Return all subjects and the topics under each one for the authenticated user."""
    user, err = auth_required()
    if err:
        return err

    conn = get_db()
    subjects = conn.execute(
        "SELECT * FROM subjects WHERE user_id = ? ORDER BY id",
        (user["id"],),
    ).fetchall()

    result = []
    for subject in subjects:
        topics = conn.execute(
            "SELECT * FROM topics WHERE subject_id = ? ORDER BY id",
            (subject["id"],),
        ).fetchall()
        result.append({**dict(subject), "topics": [dict(topic) for topic in topics]})

    conn.close()
    return jsonify({"subjects": result})


@subjects_bp.route("/", methods=["POST"])
def add_subject():
    """Add a subject for the current user."""
    user, err = auth_required()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    name = (data.get("subject_name") or "").strip()
    if not name:
        return jsonify({"error": "subject_name is required"}), 400

    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO subjects (user_id, subject_name) VALUES (?, ?)",
        (user["id"], name),
    )
    conn.commit()
    subject_id = cursor.lastrowid
    conn.close()

    return (
        jsonify({"message": "Subject added", "id": subject_id, "subject_name": name}),
        201,
    )


@subjects_bp.route("/<int:subject_id>", methods=["DELETE"])
def delete_subject(subject_id):
    """Delete a subject and its associated topics for the authenticated user."""
    user, err = auth_required()
    if err:
        return err

    conn = get_db()
    conn.execute(
        "DELETE FROM subjects WHERE id = ? AND user_id = ?",
        (subject_id, user["id"]),
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Subject deleted"})


@subjects_bp.route("/<int:subject_id>/topics", methods=["POST"])
def add_topic(subject_id):
    """Add a new study topic under a subject."""
    user, err = auth_required()
    if err:
        return err

    conn = get_db()
    subject = conn.execute(
        "SELECT id FROM subjects WHERE id = ? AND user_id = ?",
        (subject_id, user["id"]),
    ).fetchone()
    if not subject:
        conn.close()
        return jsonify({"error": "Subject not found"}), 404

    data = request.get_json(silent=True) or {}
    topic_name = (data.get("topic_name") or "").strip()
    difficulty = data.get("difficulty", "Medium")

    if not topic_name:
        conn.close()
        return jsonify({"error": "topic_name is required"}), 400
    if difficulty not in ("Easy", "Medium", "Hard"):
        difficulty = "Medium"

    cursor = conn.execute(
        "INSERT INTO topics (subject_id, topic_name, difficulty) VALUES (?, ?, ?)",
        (subject_id, topic_name, difficulty),
    )
    conn.commit()
    topic_id = cursor.lastrowid
    conn.close()

    return (
        jsonify(
            {
                "message": "Topic added",
                "id": topic_id,
                "topic_name": topic_name,
                "difficulty": difficulty,
            }
        ),
        201,
    )


@subjects_bp.route("/topics/<int:topic_id>", methods=["PATCH"])
def update_topic(topic_id):
    """Toggle or update a topic's completion status and metadata."""
    user, err = auth_required()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    completed = 1 if data.get("completed") else 0

    conn = get_db()
    row = conn.execute(
        """
        SELECT t.id
        FROM topics t
        JOIN subjects s ON s.id = t.subject_id
        WHERE t.id = ? AND s.user_id = ?
        """,
        (topic_id, user["id"]),
    ).fetchone()

    if not row:
        conn.close()
        return jsonify({"error": "Topic not found"}), 404

    conn.execute("UPDATE topics SET completed = ? WHERE id = ?", (completed, topic_id))
    conn.commit()
    conn.close()
    return jsonify({"message": "Topic updated"})


@subjects_bp.route("/topics/<int:topic_id>", methods=["DELETE"])
def delete_topic(topic_id):
    """Delete a topic under a subject that belongs to the authenticated user."""
    user, err = auth_required()
    if err:
        return err

    conn = get_db()
    conn.execute(
        """
        DELETE FROM topics
        WHERE id = ?
          AND subject_id IN (SELECT id FROM subjects WHERE user_id = ?)
        """,
        (topic_id, user["id"]),
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Topic deleted"})
