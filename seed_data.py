"""
seed_data.py  —  StudySaathi Demo Seeder
=========================================
Creates a demo user with sample data for testing / hackathon demo.

Run:  cd backend && python seed_data.py
"""

import sys, os

sys.path.insert(0, os.path.dirname(__file__))

from database import init_db, get_db
from models import hash_password, create_token
from datetime import date, timedelta
import json


def seed():
    init_db()
    conn = get_db()

    # ── Demo user ─────────────────────────────────────────────────
    email = "demo@studysaathi.in"
    existing = conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
    if existing:
        user_id = existing["id"]
        print(f"[SEED] Demo user already exists (id={user_id}). Re-seeding data…")
        # Clear old data
        conn.execute("DELETE FROM tasks    WHERE user_id=?", (user_id,))
        conn.execute("DELETE FROM progress WHERE user_id=?", (user_id,))
        conn.execute("DELETE FROM exams    WHERE user_id=?", (user_id,))
        conn.execute("DELETE FROM study_plans WHERE user_id=?", (user_id,))
        # Remove topics+subjects
        subj_ids = [
            r["id"]
            for r in conn.execute(
                "SELECT id FROM subjects WHERE user_id=?", (user_id,)
            ).fetchall()
        ]
        for sid in subj_ids:
            conn.execute("DELETE FROM topics WHERE subject_id=?", (sid,))
        conn.execute("DELETE FROM subjects WHERE user_id=?", (user_id,))
    else:
        cur = conn.execute(
            "INSERT INTO users (name, email, password, course) VALUES (?,?,?,?)",
            (
                "Manas Kumar Mishra",
                email,
                hash_password("demo1234"),
                "B.Tech / Engineering",
            ),
        )
        user_id = cur.lastrowid
        print(f"[SEED] Created demo user (id={user_id})")

    # ── Subjects + Topics ─────────────────────────────────────────
    subjects = [
        (
            "Mathematics",
            [
                ("Matrices & Determinants", "Easy", 1),
                ("Differential Calculus", "Hard", 0),
                ("Integral Calculus", "Hard", 0),
                ("Probability & Statistics", "Medium", 0),
            ],
        ),
        (
            "Physics",
            [
                ("Mechanics", "Easy", 1),
                ("Optics & Waves", "Hard", 0),
                ("Quantum Mechanics", "Hard", 0),
                ("Thermodynamics", "Medium", 1),
            ],
        ),
        (
            "DSA (Java)",
            [
                ("Arrays & Strings", "Medium", 1),
                ("Linked Lists", "Medium", 1),
                ("Trees & Graphs", "Hard", 0),
                ("DP & Backtracking", "Hard", 0),
            ],
        ),
        (
            "Operating Systems",
            [
                ("Process Management", "Medium", 1),
                ("Memory Management", "Hard", 0),
                ("File Systems", "Medium", 0),
                ("Deadlocks", "Hard", 0),
            ],
        ),
        (
            "DBMS",
            [
                ("ER Diagrams", "Easy", 1),
                ("Normalization", "Medium", 1),
                ("SQL Queries", "Medium", 1),
                ("Transactions", "Hard", 0),
            ],
        ),
    ]

    for subj_name, topics in subjects:
        cur = conn.execute(
            "INSERT INTO subjects (user_id, subject_name) VALUES (?,?)",
            (user_id, subj_name),
        )
        subj_id = cur.lastrowid
        for topic_name, difficulty, completed in topics:
            conn.execute(
                "INSERT INTO topics (subject_id, topic_name, difficulty, completed) VALUES (?,?,?,?)",
                (subj_id, topic_name, difficulty, completed),
            )
    print("[SEED] Subjects & topics added")

    # ── Tasks (today) ─────────────────────────────────────────────
    today = str(date.today())
    tasks = [
        ("Solve 10 Differential Calculus problems", "High", "pending"),
        ("Read Chapter 4 – Optics (Physics)", "High", "done"),
        ("DSA: Implement Binary Search Tree", "High", "pending"),
        ("Review OS lecture slides", "Low", "done"),
        ("Complete DBMS assignment – ER diagrams", "Medium", "pending"),
        ("Practice 5 Java coding problems", "Medium", "pending"),
        ("Make revision notes – Quantum Mechanics", "High", "pending"),
        ("Watch lecture: Integral Calculus", "Medium", "done"),
    ]
    for task, priority, status in tasks:
        conn.execute(
            "INSERT INTO tasks (user_id, task, priority, status, date) VALUES (?,?,?,?,?)",
            (user_id, task, priority, status, today),
        )
    print("[SEED] Today's tasks added")

    # ── Exams ─────────────────────────────────────────────────────
    exams = [
        (
            "Mathematics End-Term",
            (date.today() + timedelta(days=14)).isoformat(),
            "Chapters 1-6",
        ),
        (
            "DSA Mid-Semester",
            (date.today() + timedelta(days=23)).isoformat(),
            "Arrays to Trees",
        ),
        (
            "OS Lab Practical",
            (date.today() + timedelta(days=32)).isoformat(),
            "Shell scripting",
        ),
        (
            "DBMS Theory Paper",
            (date.today() + timedelta(days=40)).isoformat(),
            "Full syllabus",
        ),
    ]
    for subject, exam_date, notes in exams:
        conn.execute(
            "INSERT INTO exams (user_id, subject, exam_date, notes) VALUES (?,?,?,?)",
            (user_id, subject, exam_date, notes),
        )
    print("[SEED] Exams added")

    # ── Progress (last 10 days) ───────────────────────────────────
    progress_data = [
        # (days_ago, subject, hours)
        (0, "Mathematics", 3.5),
        (0, "DSA (Java)", 2.0),
        (1, "Physics", 4.0),
        (1, "Mathematics", 2.5),
        (2, "DBMS", 3.0),
        (2, "DSA (Java)", 1.5),
        (3, "Mathematics", 3.0),
        (3, "Physics", 2.0),
        (4, "Operating Systems", 2.5),
        (4, "Mathematics", 1.5),
        (5, "DSA (Java)", 3.0),
        (5, "Physics", 1.5),
        (6, "DBMS", 2.0),
        (6, "Mathematics", 2.5),
        # gaps to make it realistic
        (8, "DSA (Java)", 1.5),
        (9, "Physics", 2.0),
    ]
    for days_ago, subject, hours in progress_data:
        d = (date.today() - timedelta(days=days_ago)).isoformat()
        conn.execute(
            "INSERT INTO progress (user_id, subject, hours_studied, date) VALUES (?,?,?,?)",
            (user_id, subject, hours, d),
        )
    print("[SEED] Progress data added")

    conn.commit()
    conn.close()

    # Create a token so we can show the API
    token = create_token(user_id)

    print("\n" + "=" * 55)
    print("  ✅  SEED COMPLETE")
    print("=" * 55)
    print(f"  Email   : {email}")
    print(f"  Password: demo1234")
    print(f"  Token   : {token[:20]}…  (valid 7 days)")
    print("=" * 55)
    print("\n  Open frontend/login.html and log in with above creds.")


if __name__ == "__main__":
    seed()
