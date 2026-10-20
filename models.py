"""Security and identity helpers for the StudySaathi app.

This file contains the password hashing logic and token-based authentication used
by the application endpoints.
"""

import hashlib
import secrets

from database import get_db


def hash_password(plain: str) -> str:
    """Hash a plain-text password using a unique per-user salt."""
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + plain).encode("utf-8")).hexdigest()
    return f"{salt}:{hashed}"


def verify_password(plain: str, stored: str) -> bool:
    """Check a password against the stored salted hash."""
    try:
        salt, hashed = stored.split(":", 1)
        candidate = hashlib.sha256((salt + plain).encode("utf-8")).hexdigest()
        return candidate == hashed
    except (AttributeError, ValueError):
        return False


def create_token(user_id: int) -> str:
    """Create a random login token and persist it for the user."""
    token = secrets.token_hex(32)
    conn = get_db()
    conn.execute(
        "INSERT INTO tokens (token, user_id) VALUES (?, ?)",
        (token, user_id),
    )
    conn.commit()
    conn.close()
    return token


def get_user_from_token(token: str) -> dict | None:
    """Return the validated user record for a token or None if the token is invalid."""
    if not token:
        return None

    conn = get_db()
    row = conn.execute(
        """
        SELECT u.id, u.name, u.email, u.course
        FROM tokens t
        JOIN users u ON u.id = t.user_id
        WHERE t.token = ?
          AND t.created_at > datetime('now', '-7 days')
        """,
        (token,),
    ).fetchone()
    conn.close()

    return dict(row) if row else None


def delete_token(token: str):
    """Delete a token during logout."""
    conn = get_db()
    conn.execute("DELETE FROM tokens WHERE token = ?", (token,))
    conn.commit()
    conn.close()


# Compatibility aliases for the legacy backend implementation.
def hash_pw(pw):
    """Backward-compatible wrapper used by the legacy backend app."""
    return hash_password(pw)


def check_pw(pw, stored):
    """Backward-compatible password verifier for the legacy backend app."""
    return verify_password(pw, stored)


def make_token(uid, name, email):
    """Generate a signed JWT-like token with an expiration window."""
    import base64
    import hashlib
    import hmac
    import json
    import time
    import os

    secret = os.environ.get("SS3_SECRET", "studysaathi-v3-secret-key-change-in-prod")
    payload = {
        "id": uid,
        "name": name,
        "email": email,
        "exp": int(time.time()) + 86400 * 14,
    }
    encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    signature = hmac.new(secret.encode(), encoded.encode(), hashlib.sha256).hexdigest()
    return f"{encoded}.{signature}"


def verify_token(token):
    """Validate a signed token and return its payload."""
    import base64
    import hashlib
    import hmac
    import json
    import time
    import os

    secret = os.environ.get("SS3_SECRET", "studysaathi-v3-secret-key-change-in-prod")
    try:
        data, sig = token.rsplit(".", 1)
        expected = hmac.new(secret.encode(), data.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        payload = json.loads(base64.urlsafe_b64decode(data + "=="))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


def auth_required(f):
    """Decorator for legacy backend routes that expect a JWT-style token flow."""
    from functools import wraps
    from flask import jsonify, request

    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
        user = verify_token(token)
        if not user:
            return jsonify({"error": "Unauthorized"}), 401
        return f(user, *args, **kwargs)

    return wrapper
