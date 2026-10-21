"""SQLite database configuration for the backend service.

The backend uses a dedicated database directory and keeps schema setup in one place
so the app can boot cleanly with minimal dependency configuration.
"""

import os
import sqlite3

DB_PATH = os.path.join(
    os.path.dirname(__file__),
    "../database/studysaathi.db",
)

# Tests set SS3_DB_PATH to point the whole app at a throwaway database file so
# they never touch the real one. The override is read lazily (not at import
# time) so the environment can be changed before the first connection.
DEFAULT_DB_PATH = os.path.abspath(DB_PATH)


def db_path():
    """Return the active database file, honouring the SS3_DB_PATH override."""
    return os.path.abspath(os.environ.get("SS3_DB_PATH") or DEFAULT_DB_PATH)


def get_db():
    """Return a SQLite connection with row-based access enabled."""
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create the database and required tables when the backend starts."""
    os.makedirs(os.path.dirname(db_path()), exist_ok=True)
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            course TEXT DEFAULT '',
            semester INTEGER DEFAULT 1,
            exam TEXT DEFAULT '',
            daily_goal INTEGER DEFAULT 6,
            streak INTEGER DEFAULT 0,
            study_days INTEGER DEFAULT 0,
            pyq_answered INTEGER DEFAULT 0,
            plans_gen INTEGER DEFAULT 0,
            created_at TEXT DEFAULT(datetime('now')),
            email_verified INTEGER DEFAULT 0,
            verification_token TEXT DEFAULT '',
            last_login_date TEXT DEFAULT '',
            is_admin INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            created_at TEXT DEFAULT(datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            priority TEXT DEFAULT 'Medium',
            status TEXT DEFAULT 'not_started',
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT(datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            task TEXT NOT NULL,
            priority TEXT DEFAULT 'Medium',
            status TEXT DEFAULT 'pending',
            date TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            subject TEXT NOT NULL,
            exam_date TEXT NOT NULL,
            notes TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            subject TEXT NOT NULL,
            hours REAL NOT NULL,
            notes TEXT DEFAULT '',
            date TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS pyqs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            subject TEXT NOT NULL,
            exam TEXT NOT NULL,
            year INTEGER NOT NULL,
            unit TEXT DEFAULT '',
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            difficulty TEXT DEFAULT 'Medium',
            frequency INTEGER DEFAULT 1,
            importance INTEGER DEFAULT 70,
            is_verified INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            test_id INTEGER NOT NULL,
            test_title TEXT NOT NULL,
            correct INTEGER,
            wrong INTEGER,
            skipped INTEGER,
            total INTEGER,
            obtained INTEGER,
            total_marks INTEGER,
            pct INTEGER,
            time_taken INTEGER,
            grade TEXT,
            date TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS study_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            exam_date TEXT NOT NULL,
            mode TEXT DEFAULT 'balanced',
            daily_hours INTEGER,
            plan_json TEXT NOT NULL,
            created_at TEXT DEFAULT(datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            kind TEXT DEFAULT 'request',
            rating INTEGER DEFAULT 0,
            title TEXT DEFAULT '',
            message TEXT NOT NULL,
            status TEXT DEFAULT 'new',
            admin_note TEXT DEFAULT '',
            created_at TEXT DEFAULT(datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            event TEXT NOT NULL,
            detail TEXT DEFAULT '',
            created_at TEXT DEFAULT(datetime('now'))
        );
        """)
    db.commit()

    # Migration: add last_login_date column to existing users tables
    try:
        db.execute("ALTER TABLE users ADD COLUMN last_login_date TEXT DEFAULT ''")
    except Exception:
        pass  # Column already exists

    # Migration: add is_admin column to existing users tables
    try:
        db.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
    except Exception:
        pass  # Column already exists

    db.close()
    bootstrap_admin(db_path=db_path())
    print(f"✅ Database initialised: {db_path()}")


def bootstrap_admin(db_path=None, email=None):
    """Promote a user to administrator.

    Bootstrap order (first match wins):
      1. explicit ``email`` argument
      2. ``ADMIN_EMAIL`` environment variable
      3. ``ADMIN_USER_ID`` environment variable

    The promotion only happens when the target user already exists, so this is
    safe to call on every startup. It never grants admin to unknown accounts.
    """
    email = (email or os.environ.get("ADMIN_EMAIL") or "").strip().lower()
    uid = os.environ.get("ADMIN_USER_ID")

    if not email and not uid:
        return None

    db = get_db()
    try:
        if email:
            row = db.execute(
                "SELECT id, name, is_admin FROM users WHERE LOWER(email) = ?",
                [email],
            ).fetchone()
            if not row:
                print(f"⚠️  Admin bootstrap skipped — no user with email {email}")
                return None
            target_id = row["id"]
            label = row["name"]
        else:
            row = db.execute(
                "SELECT id, name FROM users WHERE id = ?", [int(uid)]
            ).fetchone()
            if not row:
                print(f"⚠️  Admin bootstrap skipped — no user with id {uid}")
                return None
            target_id = row["id"]
            label = row["name"]

        if row["is_admin"] if "is_admin" in row.keys() else False:
            print(f"✅ Admin already set: {label}")
            return target_id

        db.execute("UPDATE users SET is_admin = 1 WHERE id = ?", [target_id])
        db.commit()
        print(f"👑 Admin granted to: {label} (#{target_id})")
        return target_id
    finally:
        db.close()
