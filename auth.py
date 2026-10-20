"""Authentication endpoints for StudySaathi.

These routes are responsible for account creation, login, logout, and user lookup
from the bearer token.
"""

from flask import Blueprint, jsonify, request

from database import get_db
from models import (
    create_token,
    delete_token,
    get_user_from_token,
    hash_password,
    verify_password,
)

auth_bp = Blueprint("auth", __name__)


def get_token_from_header():
    """Return the request token from the Authorization header if present."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.replace("Bearer ", "", 1).strip()
    return None


def _safe_json():
    """Return a parsed JSON payload or an empty dict when the body is absent."""
    return request.get_json(silent=True) or {}


@auth_bp.route("/register", methods=["POST"])
def register():
    """Create a new user account and return a token."""
    data = _safe_json()
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "").strip()
    course = (data.get("course") or "").strip()

    if not name or not email or not password:
        return jsonify({"error": "Name, email and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    conn = get_db()
    existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        conn.close()
        return jsonify({"error": "Email already registered"}), 409

    hashed_password = hash_password(password)
    cursor = conn.execute(
        "INSERT INTO users (name, email, password, course) VALUES (?, ?, ?, ?)",
        (name, email, hashed_password, course),
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    token = create_token(user_id)
    return (
        jsonify(
            {
                "message": "Account created successfully",
                "token": token,
                "user": {"id": user_id, "name": name, "email": email, "course": course},
            }
        ),
        201,
    )


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate an existing user and return a valid token."""
    data = _safe_json()
    email = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "").strip()

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()

    if not user or not verify_password(password, user["password"]):
        return jsonify({"error": "Invalid email or password"}), 401

    token = create_token(user["id"])
    return jsonify(
        {
            "message": "Login successful",
            "token": token,
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "course": user["course"],
            },
        }
    )


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Invalidate the current bearer token if one exists."""
    token = get_token_from_header()
    if token:
        delete_token(token)
    return jsonify({"message": "Logged out"})


@auth_bp.route("/me", methods=["GET"])
def me():
    """Return the current authenticated user's public information."""
    token = get_token_from_header()
    user = get_user_from_token(token)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"user": user})
