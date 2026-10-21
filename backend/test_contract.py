"""Verify the admin API response shape matches what frontend/admin.html expects.

Runs against a throwaway database so the real dev data is never touched.
"""

from test_support import cleanup_db, isolate_db

_TEST_DB = isolate_db("ss3_contract_")

import app as ba  # noqa: E402  (must import after the DB path is set)
from database import get_db, init_db  # noqa: E402


def make_user(email, name="Test User", admin=False, course="btech-cse"):
    db = get_db()
    db.execute(
        "INSERT INTO users(name, email, password, course, semester, exam) "
        "VALUES(?, ?, 'x', ?, 3, 'GATE')",
        [name, email, course],
    )
    db.commit()
    uid = db.execute("SELECT id FROM users WHERE email=?", [email]).fetchone()["id"]
    if admin:
        db.execute("UPDATE users SET is_admin=1 WHERE id=?", [uid])
        db.commit()
    db.close()
    token = ba.make_token(uid, name, email)
    return uid, token


def main():
    init_db()
    c = ba.app.test_client()

    db = get_db()
    for t in ("activity_log", "feedback", "users"):
        db.execute(f"DELETE FROM {t}")
    db.commit()
    db.close()

    uid_a, tok_a = make_user("admin@test.com", "Admin Boss", admin=True)
    uid_u, tok_u = make_user("user@test.com", "Normal User", course="btech-ece")
    ha = {"Authorization": f"Bearer {tok_a}"}
    hu = {"Authorization": f"Bearer {tok_u}"}

    # Give the admin a course + some feedback so charts have data.
    db = get_db()
    db.execute(
        "INSERT INTO feedback(user_id, kind, rating, title, message) "
        "VALUES(?, 'review', 5, 'Great app', 'Love it')",
        [uid_u],
    )
    db.commit()
    db.close()

    problems = []

    def want(name, cond, extra=""):
        print(("OK   " if cond else "FAIL ") + name + ("" if cond else f"  <- {extra}"))
        if not cond:
            problems.append(name)

    # ---- Overview contract ----
    d = c.get("/api/admin/overview", headers=ha).get_json()
    want("overview has 'stats'", "stats" in d, list(d.keys()))
    want("overview has 'courses'", "courses" in d, list(d.keys()))
    want("overview has 'signups'", "signups" in d, list(d.keys()))
    want("overview has 'feedback_kinds'", "feedback_kinds" in d, list(d.keys()))
    want("overview has 'activity'", "activity" in d, list(d.keys()))
    want("overview activity is a list", isinstance(d.get("activity"), list), type(d.get("activity")))

    st = d.get("stats", {})
    for k in (
        "total_users",
        "new_users",
        "total_feedback",
        "pending_feedback",
        "avg_rating",
    ):
        want(f"stats.{k} present", k in st, list(st.keys()))

    courses = d.get("courses") or []
    want("courses is a list", isinstance(courses, list), type(courses))
    want(
        "courses entries have l/v",
        all("l" in x and "v" in x for x in courses),
        courses[:2],
    )
    sg = d.get("signups") or []
    want("signups entries have l/v", all("l" in x and "v" in x for x in sg), sg[:2])

    # ---- Users contract ----
    users = c.get("/api/admin/users", headers=ha).get_json()["users"]
    want("users list non-empty", len(users) > 0, len(users))
    u = users[0]
    for k in (
        "id",
        "name",
        "email",
        "course",
        "semester",
        "is_admin",
        "created_at",
        "streak",
        "c_subjects",
        "c_tests",
        "c_hours",
    ):
        want(f"user.{k} present", k in u, sorted(u.keys()))

    # ---- Filters ----
    f = c.get("/api/admin/feedback?status=new", headers=ha).get_json()["feedback"]
    want("feedback status filter works", all(x["status"] == "new" for x in f), f)
    f2 = c.get("/api/admin/feedback?kind=review", headers=ha).get_json()["feedback"]
    want("feedback kind filter works", all(x["kind"] == "review" for x in f2), f2)
    su = c.get("/api/admin/users?q=Normal", headers=ha).get_json()["users"]
    want("user q filter works", len(su) == 1 and su[0]["email"] == "user@test.com", su)
    au = c.get("/api/admin/users?is_admin=1", headers=ha).get_json()["users"]
    want("user is_admin filter works", all(x["is_admin"] for x in au), au)

    # ---- Activity contract ----
    act = c.get("/api/admin/activity", headers=ha).get_json()["activity"]
    want("activity is a list", isinstance(act, list), type(act))
    want(
        "activity entries have event/created_at/uname",
        all("event" in a and "created_at" in a for a in act),
        act[:1],
    )

    # ---- Feedback shape ----
    fb = c.get("/api/admin/feedback", headers=ha).get_json()["feedback"]
    want("feedback non-empty", len(fb) > 0, len(fb))
    f0 = fb[0]
    for k in ("id", "kind", "rating", "title", "message", "status", "admin_note", "created_at"):
        want(f"feedback.{k} present", k in f0, sorted(f0.keys()))
    want("feedback has uname", "uname" in f0, sorted(f0.keys()))

    # ---- Self-demotion / self-delete guard ----
    r = c.patch(f"/api/admin/users/{uid_a}", headers=ha, json={"is_admin": False})
    want("self-demotion blocked", r.status_code == 400, r.status_code)
    r = c.patch(f"/api/admin/users/{uid_a}", headers=ha, json={"delete": True})
    want("self-deletion blocked", r.status_code == 400, r.status_code)

    cleanup_db(_TEST_DB)

    print()
    if problems:
        print(f"{len(problems)} CONTRACT PROBLEM(S): {problems}")
        return 1
    print("ALL ADMIN API CONTRACTS OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
