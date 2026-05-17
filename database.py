"""
database.py
-----------
Handles SQLite connection and table initialization for StudySaathi.
Uses Python's built-in sqlite3 — no external ORM needed.
"""

import sqlite3
import os

# ── DB file location (sits next to this script) ──────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "studysaathi.db")


def get_db():
    """Return a new SQLite connection with row_factory set to Row (dict-like)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # lets us do row["column_name"]
    conn.execute("PRAGMA foreign_keys = ON") # enforce FK constraints
    return conn


def init_db():
    """
    Create all tables if they don't already exist.
    Called once at app startup.
    """
    conn = get_db()
    c = conn.cursor()

    # ── Users ────────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            email       TEXT    NOT NULL UNIQUE,
            password    TEXT    NOT NULL,   -- SHA-256 salted hash
            course      TEXT,
            created_at  TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── Auth tokens (simple token table instead of JWT) ───────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS tokens (
            token       TEXT    PRIMARY KEY,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at  TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── Subjects ─────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            subject_name TEXT    NOT NULL,
            created_at   TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── Topics (per subject) ─────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id  INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
            topic_name  TEXT    NOT NULL,
            difficulty  TEXT    DEFAULT 'Medium',   -- Easy / Medium / Hard
            completed   INTEGER DEFAULT 0           -- 0 = pending, 1 = done
        )
    """)

    # ── Tasks ────────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            task     TEXT    NOT NULL,
            notes    TEXT,
            status   TEXT    DEFAULT 'pending',     -- pending / done
            priority TEXT    DEFAULT 'Medium',      -- High / Medium / Low
            date     TEXT    DEFAULT (date('now'))
        )
    """)

    # ── Exams ────────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS exams (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            subject    TEXT    NOT NULL,
            exam_date  TEXT    NOT NULL,
            notes      TEXT,
            created_at TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── Progress ─────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            subject       TEXT    NOT NULL,
            hours_studied REAL    DEFAULT 0,
            date          TEXT    DEFAULT (date('now'))
        )
    """)

    # ── Study Plans (generated / saved) ──────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS study_plans (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            exam_date   TEXT    NOT NULL,
            daily_hours REAL    NOT NULL,
            plan_json   TEXT    NOT NULL,    -- JSON blob of the generated plan
            created_at  TEXT    DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] Tables initialised at", DB_PATH)
