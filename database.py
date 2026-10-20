"""Database layer for the StudySaathi app.

This module centralizes the SQLite connection and schema setup so the rest of the
application can safely interact with the database without repeating boilerplate.
"""

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "studysaathi.db")


def get_db():
    """Create and return a SQLite connection configured for Row-based access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create every required table if it does not already exist."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            email      TEXT NOT NULL UNIQUE,
            password   TEXT NOT NULL,
            course     TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tokens (
            token      TEXT PRIMARY KEY,
            user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at TEXT DEFAULT (datetime('now'))
        )
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            subject_name TEXT NOT NULL,
            created_at   TEXT DEFAULT (datetime('now'))
        )
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
            topic_name TEXT NOT NULL,
            difficulty TEXT DEFAULT 'Medium',
            completed  INTEGER DEFAULT 0
        )
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            task     TEXT NOT NULL,
            notes    TEXT,
            status   TEXT DEFAULT 'pending',
            priority TEXT DEFAULT 'Medium',
            date     TEXT DEFAULT (date('now'))
        )
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exams (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            subject    TEXT NOT NULL,
            exam_date  TEXT NOT NULL,
            notes      TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            subject       TEXT NOT NULL,
            hours_studied REAL DEFAULT 0,
            date          TEXT DEFAULT (date('now'))
        )
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS study_plans (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            exam_date   TEXT NOT NULL,
            daily_hours REAL NOT NULL,
            plan_json   TEXT NOT NULL,
            created_at  TEXT DEFAULT (datetime('now'))
        )
        """)

    conn.commit()
    conn.close()
    print(f"[DB] Tables initialised at {DB_PATH}")
