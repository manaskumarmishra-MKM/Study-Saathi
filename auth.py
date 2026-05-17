"""
routes/auth.py
--------------
Endpoints:
  POST /api/auth/register  — create account
  POST /api/auth/login     — get token
  POST /api/auth/logout    — invalidate token
  GET  /api/auth/me        — get current user info
"""

from flask import Blueprint, request, jsonify
from database import get_db
from models import hash_password, verify_password, create_token, get_user_from_token, delete_token

auth_bp = Blueprint("auth", __name__)


# ── Helper: extract Bearer token from Authorization header ───────────────────
def get_token_from_header():
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return None


# ── Register ──────────────────────────────────────────────────────────────────
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    name     = (data.get("name",     "") or "").strip()
    email    = (data.get("email",    "") or "").strip().lower()
    password = (data.get("password", "") or "").strip()
    course   = (data.get("course",   "") or "").strip()

    # ── Validation ───────────────────────────────────────────────────────────
    if not name or not email or not password:
        return jsonify({"error": "Name, email and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM users WHERE email = ?", (email,)
    ).fetchone()

    if existing:
        conn.close()
        return jsonify({"error": "Email already registered"}), 409

    hashed_pw = hash_password(password)
    cursor = conn.execute(
        "INSERT INTO users (name, email, password, course) VALUES (?, ?, ?, ?)",
        (name, email, hashed_pw, course)
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    token = create_token(user_id)
    return jsonify({
        "message": "Account created successfully",
        "token":   token,
        "user":    {"id": user_id, "name": name, "email": email, "course": course}
    }), 201


# ── Login ─────────────────────────────────────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    data     = request.get_json()
    email    = (data.get("email",    "") or "").strip().lower()
    password = (data.get("password", "") or "").strip()

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()
    conn.close()

    if not user or not verify_password(password, user["password"]):
        return jsonify({"error": "Invalid email or password"}), 401

    token = create_token(user["id"])
    return jsonify({
        "message": "Login successful",
        "token":   token,
        "user": {
            "id":     user["id"],
            "name":   user["name"],
            "email":  user["email"],
            "course": user["course"]
        }
    })


# ── Logout ────────────────────────────────────────────────────────────────────
@auth_bp.route("/logout", methods=["POST"])
def logout():
    token = get_token_from_header()
    if token:
        delete_token(token)
    return jsonify({"message": "Logged out"})


# ── Me ────────────────────────────────────────────────────────────────────────
@auth_bp.route("/me", methods=["GET"])
def me():
    token = get_token_from_header()
    user  = get_user_from_token(token)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"user": user})
