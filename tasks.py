"""
routes/tasks.py
---------------
Endpoints:
  GET    /api/tasks/          — list tasks (filter by ?date=YYYY-MM-DD)
  POST   /api/tasks/          — create task
  PATCH  /api/tasks/<id>      — update task (status, notes, etc.)
  DELETE /api/tasks/<id>      — delete task
"""

from flask import Blueprint, request, jsonify
from database import get_db
from models import get_user_from_token
from datetime import date

tasks_bp = Blueprint("tasks", __name__)


def auth_required():
    token = (request.headers.get("Authorization", "") or "").replace("Bearer ", "")
    user  = get_user_from_token(token)
    if not user:
        return None, (jsonify({"error": "Unauthorized"}), 401)
    return user, None


# ── List tasks ─────────────────────────────────────────────────────────────────
@tasks_bp.route("/", methods=["GET"])
def list_tasks():
    user, err = auth_required()
    if err: return err

    filter_date = request.args.get("date") or str(date.today())

    conn = get_db()
    tasks = conn.execute(
        "SELECT * FROM tasks WHERE user_id = ? AND date = ? ORDER BY id DESC",
        (user["id"], filter_date)
    ).fetchall()
    conn.close()

    return jsonify({
        "tasks": [dict(t) for t in tasks],
        "date":  filter_date
    })


# ── Create task ────────────────────────────────────────────────────────────────
@tasks_bp.route("/", methods=["POST"])
def create_task():
    user, err = auth_required()
    if err: return err

    data     = request.get_json()
    task_txt = (data.get("task") or "").strip()
    notes    = (data.get("notes") or "").strip()
    priority = data.get("priority", "Medium")
    task_date = data.get("date") or str(date.today())

    if not task_txt:
        return jsonify({"error": "task text required"}), 400
    if priority not in ("High", "Medium", "Low"):
        priority = "Medium"

    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO tasks (user_id, task, notes, priority, date) VALUES (?, ?, ?, ?, ?)",
        (user["id"], task_txt, notes, priority, task_date)
    )
    conn.commit()
    task_id = cursor.lastrowid
    conn.close()

    return jsonify({
        "message":  "Task created",
        "id":       task_id,
        "task":     task_txt,
        "status":   "pending",
        "priority": priority,
        "date":     task_date
    }), 201


# ── Update task ────────────────────────────────────────────────────────────────
@tasks_bp.route("/<int:task_id>", methods=["PATCH"])
def update_task(task_id):
    user, err = auth_required()
    if err: return err

    data = request.get_json()

    conn = get_db()
    existing = conn.execute(
        "SELECT * FROM tasks WHERE id = ? AND user_id = ?", (task_id, user["id"])
    ).fetchone()

    if not existing:
        conn.close()
        return jsonify({"error": "Task not found"}), 404

    # Merge existing values with updates
    status   = data.get("status",   existing["status"])
    notes    = data.get("notes",    existing["notes"])
    priority = data.get("priority", existing["priority"])
    task_txt = data.get("task",     existing["task"])

    conn.execute(
        "UPDATE tasks SET status=?, notes=?, priority=?, task=? WHERE id=?",
        (status, notes, priority, task_txt, task_id)
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Task updated"})


# ── Delete task ────────────────────────────────────────────────────────────────
@tasks_bp.route("/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    user, err = auth_required()
    if err: return err

    conn = get_db()
    conn.execute(
        "DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user["id"])
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Task deleted"})
