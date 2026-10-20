"""Task routes for StudySaathi.

These endpoints allow authenticated users to view, create, update, and delete
study tasks for a selected date.
"""

from datetime import date

from flask import Blueprint, jsonify, request

from database import get_db
from models import get_user_from_token

tasks_bp = Blueprint("tasks", __name__)


def auth_required():
    """Return the current user or a 401 error response."""
    token = (request.headers.get("Authorization", "") or "").replace("Bearer ", "")
    user = get_user_from_token(token)
    if not user:
        return None, (jsonify({"error": "Unauthorized"}), 401)
    return user, None


@tasks_bp.route("/", methods=["GET"])
def list_tasks():
    """List all tasks for the current user on the selected date."""
    user, err = auth_required()
    if err:
        return err

    filter_date = request.args.get("date") or str(date.today())

    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM tasks WHERE user_id = ? AND date = ? ORDER BY id DESC",
        (user["id"], filter_date),
    ).fetchall()
    conn.close()

    return jsonify({"tasks": [dict(row) for row in rows], "date": filter_date})


@tasks_bp.route("/", methods=["POST"])
def create_task():
    """Create a new task for the authenticated user."""
    user, err = auth_required()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    task_text = (data.get("task") or "").strip()
    notes = (data.get("notes") or "").strip()
    priority = data.get("priority", "Medium")
    task_date = data.get("date") or str(date.today())

    if not task_text:
        return jsonify({"error": "task text required"}), 400
    if priority not in ("High", "Medium", "Low"):
        priority = "Medium"

    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO tasks (user_id, task, notes, priority, date) VALUES (?, ?, ?, ?, ?)",
        (user["id"], task_text, notes, priority, task_date),
    )
    conn.commit()
    task_id = cursor.lastrowid
    conn.close()

    return (
        jsonify(
            {
                "message": "Task created",
                "id": task_id,
                "task": task_text,
                "status": "pending",
                "priority": priority,
                "date": task_date,
            }
        ),
        201,
    )


@tasks_bp.route("/<int:task_id>", methods=["PATCH"])
def update_task(task_id):
    """Update the details of an existing task."""
    user, err = auth_required()
    if err:
        return err

    data = request.get_json(silent=True) or {}

    conn = get_db()
    existing = conn.execute(
        "SELECT * FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, user["id"]),
    ).fetchone()

    if not existing:
        conn.close()
        return jsonify({"error": "Task not found"}), 404

    status = data.get("status", existing["status"])
    notes = data.get("notes", existing["notes"])
    priority = data.get("priority", existing["priority"])
    task_text = data.get("task", existing["task"])

    conn.execute(
        "UPDATE tasks SET status=?, notes=?, priority=?, task=? WHERE id=?",
        (status, notes, priority, task_text, task_id),
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Task updated"})


@tasks_bp.route("/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    """Delete a task if it belongs to the authenticated user."""
    user, err = auth_required()
    if err:
        return err

    conn = get_db()
    conn.execute(
        "DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user["id"])
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Task deleted"})
