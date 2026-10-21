"""Authentication helpers used by the backend REST API.

These helpers keep password hashing, JWT-like token generation, and route
protection consistent across the backend service.
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from functools import wraps

from flask import jsonify, request

# Fallback used only for local development. Production deployments must set
# SS3_SECRET (see the environment table in README.md).
DEV_SECRET = "studysaathi-v3-secret-key-change-in-prod"


def secret():
    """Return the active signing key.

    The value is resolved lazily on every call instead of being captured at
    import time, so a ``.env`` file loaded by ``app.py`` (or a value exported
    after import) is always honoured — signing and verification can never end
    up using two different keys.
    """
    return os.environ.get("SS3_SECRET") or DEV_SECRET


def is_default_secret():
    """True when the app is still using the development signing key."""
    return not os.environ.get("SS3_SECRET")


def hash_pw(pw):
    """Hash a password with a unique per-user salt using PBKDF2-HMAC-SHA256."""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 310000)
    return f"{salt}:{digest.hex()}"


def check_pw(pw, stored):
    """Verify a password against its stored hash."""
    try:
        salt, hex_digest = stored.split(":", 1)
        digest = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 310000)
        return hmac.compare_digest(digest.hex(), hex_digest)
    except Exception:
        return False


def make_token(uid, name, email):
    """Create a signed JWT-like token containing the user payload."""
    payload = {
        "id": uid,
        "name": name,
        "email": email,
        "exp": int(time.time()) + 86400 * 14,
    }
    encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    signature = hmac.new(secret().encode(), encoded.encode(), hashlib.sha256).hexdigest()
    return f"{encoded}.{signature}"


def verify_token(token):
    """Validate a signed token and return the payload if still active."""
    try:
        data, sig = token.rsplit(".", 1)
        expected = hmac.new(secret().encode(), data.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None

        payload = json.loads(base64.urlsafe_b64decode(data + "=="))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


def auth_required(f):
    """Decorator that enforces bearer-token authentication for endpoint handlers."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
        user = verify_token(token)
        if not user:
            return jsonify({"error": "Unauthorized"}), 401
        return f(user, *args, **kwargs)

    return wrapper


def admin_required(f):
    """Decorator that restricts an endpoint to admin accounts only.

    The admin flag is read from the database (not the token) so that revoking
    admin rights takes effect immediately, without waiting for token expiry.
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
        user = verify_token(token)
        if not user:
            return jsonify({"error": "Unauthorized"}), 401

        from database import get_db

        db = get_db()
        row = db.execute(
            "SELECT is_admin FROM users WHERE id = ?", [user["id"]]
        ).fetchone()
        db.close()
        if not row or not row["is_admin"]:
            return jsonify({"error": "Admin access required"}), 403
        return f(user, *args, **kwargs)

    return wrapper
