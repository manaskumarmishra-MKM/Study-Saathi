"""
app.py  —  StudySaathi Backend
===============================
Entry point for the Flask application.

Run:
    cd backend
    python app.py

The server starts on http://localhost:5000
CORS is handled manually so no flask-cors dependency is needed.
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, jsonify, request, g
from database import init_db

# ── Blueprint imports ─────────────────────────────────────────────────────────
from routes.auth      import auth_bp
from routes.subjects  import subjects_bp
from routes.planner   import planner_bp
from routes.tasks     import tasks_bp
from routes.exams     import exams_bp
from routes.progress  import progress_bp

# ── App factory ───────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config["SECRET_KEY"] = "studysaathi-secret-change-in-production"

# ── Register blueprints ───────────────────────────────────────────────────────
app.register_blueprint(auth_bp,      url_prefix="/api/auth")
app.register_blueprint(subjects_bp,  url_prefix="/api/subjects")
app.register_blueprint(planner_bp,   url_prefix="/api/planner")
app.register_blueprint(tasks_bp,     url_prefix="/api/tasks")
app.register_blueprint(exams_bp,     url_prefix="/api/exams")
app.register_blueprint(progress_bp,  url_prefix="/api/progress")


# ── Manual CORS (no flask-cors dependency) ────────────────────────────────────
@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin", "*")
    response.headers["Access-Control-Allow-Origin"]  = origin
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

@app.before_request
def handle_options():
    """Handle CORS pre-flight requests."""
    if request.method == "OPTIONS":
        from flask import Response
        r = Response()
        r.headers["Access-Control-Allow-Origin"]  = request.headers.get("Origin", "*")
        r.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        r.headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, DELETE, OPTIONS"
        return r, 200


# ── Dashboard summary endpoint ────────────────────────────────────────────────
from routes.auth     import get_token_from_header
from models          import get_user_from_token
from database        import get_db
from datetime        import date

@app.route("/api/dashboard", methods=["GET"])
def dashboard():
    """
    Aggregate endpoint — returns everything the dashboard needs in one call:
    today's tasks, upcoming exams, study streak, and hours today.
    """
    token = get_token_from_header()
    user  = get_user_from_token(token)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    today_str = str(date.today())
    conn = get_db()

    # Today's tasks
    tasks = conn.execute(
        "SELECT * FROM tasks WHERE user_id=? AND date=? ORDER BY id DESC LIMIT 8",
        (user["id"], today_str)
    ).fetchall()

    # Upcoming exams (next 30 days)
    exams = conn.execute("""
        SELECT subject, exam_date,
               julianday(exam_date) - julianday('now') AS days_left
        FROM exams
        WHERE user_id=?
          AND exam_date >= date('now')
        ORDER BY exam_date ASC LIMIT 5
    """, (user["id"],)).fetchall()

    # Hours today
    hrs_row = conn.execute(
        "SELECT COALESCE(SUM(hours_studied),0) AS h FROM progress WHERE user_id=? AND date=?",
        (user["id"], today_str)
    ).fetchone()

    # Task counts
    counts = conn.execute("""
        SELECT
          COUNT(*) as total,
          SUM(CASE WHEN status='done' THEN 1 ELSE 0 END) as done
        FROM tasks WHERE user_id=? AND date=?
    """, (user["id"], today_str)).fetchone()

    # Subject count
    subj_count = conn.execute(
        "SELECT COUNT(*) as c FROM subjects WHERE user_id=?", (user["id"],)
    ).fetchone()

    # Overall topic completion %
    topic_row = conn.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN t.completed=1 THEN 1 ELSE 0 END) as done
        FROM topics t
        JOIN subjects s ON s.id = t.subject_id
        WHERE s.user_id=?
    """, (user["id"],)).fetchone()

    conn.close()

    total_t = topic_row["total"] or 0
    done_t  = topic_row["done"]  or 0
    syllabus_pct = round((done_t / total_t * 100) if total_t else 0, 1)

    return jsonify({
        "user":          user,
        "date":          today_str,
        "tasks":         [dict(t) for t in tasks],
        "exams":         [dict(e) for e in exams],
        "hours_today":   round(hrs_row["h"], 1),
        "tasks_total":   counts["total"] or 0,
        "tasks_done":    counts["done"]  or 0,
        "subject_count": subj_count["c"] or 0,
        "syllabus_pct":  syllabus_pct
    })


# ── Health check ──────────────────────────────────────────────────────────────
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "app": "StudySaathi API v1.0"})


# ── 404 handler ───────────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed"}), 405

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error", "detail": str(e)}), 500


# ── Bootstrap ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()           # create tables on first run
    print("="*50)
    print("  StudySaathi API running on http://localhost:5000")
    print("="*50)
    app.run(debug=True, host="0.0.0.0", port=5000)
