"""
models.py
---------
Business-logic helpers: password hashing, token generation/validation.
All crypto uses Python's built-in hashlib + secrets — no external deps.
"""

import hashlib
import secrets
from database import get_db


# ── Password helpers ──────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """
    Returns  salt:sha256(salt + password)
    The salt is a 32-char hex random string prepended to the stored value.
    """
    salt = secrets.token_hex(16)                # 32 hex chars
    hashed = hashlib.sha256((salt + plain).encode()).hexdigest()
    return f"{salt}:{hashed}"


def verify_password(plain: str, stored: str) -> bool:
    """Re-hash using the stored salt and compare."""
    try:
        salt, hashed = stored.split(":", 1)
        return hashlib.sha256((salt + plain).encode()).hexdigest() == hashed
    except Exception:
        return False


# ── Token helpers ─────────────────────────────────────────────────────────────

def create_token(user_id: int) -> str:
    """Generate a 64-char random token and persist it in the tokens table."""
    token = secrets.token_hex(32)               # 64 hex chars
    conn = get_db()
    conn.execute(
        "INSERT INTO tokens (token, user_id) VALUES (?, ?)",
        (token, user_id)
    )
    conn.commit()
    conn.close()
    return token


def get_user_from_token(token: str) -> dict | None:
    """
    Validate token; return the user row as a dict or None if invalid.
    Also auto-expires tokens older than 7 days.
    """
    if not token:
        return None
    conn = get_db()
    row = conn.execute("""
        SELECT u.id, u.name, u.email, u.course
        FROM tokens t
        JOIN users u ON u.id = t.user_id
        WHERE t.token = ?
          AND t.created_at > datetime('now', '-7 days')
    """, (token,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_token(token: str):
    """Remove a token on logout."""
    conn = get_db()
    conn.execute("DELETE FROM tokens WHERE token = ?", (token,))
    conn.commit()
    conn.close()
