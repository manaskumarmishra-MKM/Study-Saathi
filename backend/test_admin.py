"""Admin dashboard backend smoke test.

Run from the backend/ directory:
    python3 test_admin.py

The suite runs against a throwaway database (see test_support.isolate_db) so it
never modifies the real development data.
"""

import os

from test_support import cleanup_db, isolate_db

_TEST_DB = isolate_db("ss3_admin_")

import app as ba  # noqa: E402  (must import after the DB path is set)
from database import get_db, init_db  # noqa: E402


def make_user(email, name="Test User", admin=False):
    """Create a user directly in the DB and return (id, token)."""
    db = get_db()
    db.execute(
        "INSERT INTO users(name, email, password, course, semester, exam) "
        "VALUES(?, ?, 'x', 'btech-cse', 3, 'GATE')",
        [name, email],
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

    # Start from a clean slate so leftover dev rows don't skew counts.
    db = get_db()
    for t in ("activity_log", "feedback", "users"):
        db.execute(f"DELETE FROM {t}")
    db.commit()
    db.close()

    uid_a, tok_a = make_user("admin@test.com", "Admin Boss", admin=True)
    uid_u, tok_u = make_user("user@test.com", "Normal User")
    ha = {"Authorization": f"Bearer {tok_a}"}
    hu = {"Authorization": f"Bearer {tok_u}"}

    checks = []

    def check(name, cond, extra=""):
        checks.append((name, cond, extra))
        print(("PASS " if cond else "FAIL ") + name + ("" if cond else f"  <- {extra}"))

    # 1. Non-admin is blocked from every admin endpoint
    r = c.get("/api/admin/overview", headers=hu)
    check("non-admin blocked from overview", r.status_code == 403, r.status_code)
    r = c.get("/api/admin/users", headers=hu)
    check("non-admin blocked from users list", r.status_code == 403, r.status_code)
    r = c.get("/api/admin/feedback", headers=hu)
    check("non-admin blocked from feedback list", r.status_code == 403, r.status_code)
    r = c.get("/api/admin/activity", headers=hu)
    check("non-admin blocked from activity", r.status_code == 403, r.status_code)

    # 2. Unauthenticated is blocked
    r = c.get("/api/admin/overview")
    check("anonymous blocked", r.status_code == 401, r.status_code)

    # 3. Admin can read overview
    r = c.get("/api/admin/overview", headers=ha)
    d = r.get_json() or {}
    check("admin can read overview", r.status_code == 200, r.status_code)
    check("overview has stats", "stats" in d, list(d.keys()))
    check("overview total_users >= 2", d.get("stats", {}).get("total_users", 0) >= 2, d.get("stats"))
    check("overview has signups series", len(d.get("signups", [])) == 14, len(d.get("signups", [])))

    # 4. Feedback submission by a normal user
    r = c.post(
        "/api/feedback",
        headers=hu,
        json={"kind": "review", "rating": 5, "title": "Great app", "message": "Love it!"},
    )
    check("user can submit feedback", r.status_code == 201, r.status_code)
    fid = (r.get_json() or {}).get("feedback", {}).get("id")

    r = c.post("/api/feedback", headers=hu, json={"kind": "bug", "message": ""})
    check("empty feedback rejected", r.status_code == 400, r.status_code)

    r = c.get("/api/feedback", headers=hu)
    check("user sees own feedback", len((r.get_json() or {}).get("feedback", [])) == 1, r.get_json())

    # 5. Admin sees all feedback
    r = c.get("/api/admin/feedback", headers=ha)
    rows = (r.get_json() or {}).get("feedback", [])
    check("admin sees feedback", len(rows) == 1, len(rows))
    check("feedback has user info", rows and rows[0].get("uname") == "Normal User", rows[:1])

    # 6. Admin updates feedback status + note
    r = c.patch(f"/api/admin/feedback/{fid}", headers=ha, json={"status": "resolved", "admin_note": "Shipped in v3.1"})
    check("admin can update feedback", r.status_code == 200, r.status_code)
    check("feedback status persisted", (r.get_json() or {}).get("feedback", {}).get("status") == "resolved", r.get_json())

    r = c.get("/api/admin/feedback?status=resolved", headers=ha)
    check("feedback status filter works", len((r.get_json() or {}).get("feedback", [])) == 1, r.get_json())
    r = c.get("/api/admin/feedback?status=new", headers=ha)
    check("feedback status filter excludes others", len((r.get_json() or {}).get("feedback", [])) == 0, r.get_json())

    # 7. Admin user list
    r = c.get("/api/admin/users", headers=ha)
    users = (r.get_json() or {}).get("users", [])
    check("admin sees user list", len(users) == 2, len(users))
    check("user list has is_admin flag", any(x.get("is_admin") for x in users), users)
    check("user list has study counts", all("c_subjects" in x for x in users), users[:1])

    # 8. Admin user detail
    r = c.get(f"/api/admin/users/{uid_u}", headers=ha)
    det = r.get_json() or {}
    check("admin can read user detail", r.status_code == 200, r.status_code)
    check(
        "detail has expected sections",
        all(
            k in det
            for k in ("user", "subjects", "topics", "progress", "scores", "feedback", "activity")
        ),
        list(det.keys()),
    )

    # 9. Non-admin cannot read another user's detail
    r = c.get(f"/api/admin/users/{uid_a}", headers=hu)
    check("non-admin blocked from user detail", r.status_code == 403, r.status_code)

    # 10. Admin promotes a user; admin cannot demote self
    r = c.patch(f"/api/admin/users/{uid_u}", headers=ha, json={"is_admin": True})
    check(
        "admin can promote user",
        r.status_code == 200 and (r.get_json() or {})["user"]["is_admin"],
        r.get_json(),
    )
    r = c.patch(f"/api/admin/users/{uid_a}", headers=ha, json={"is_admin": False})
    check("admin cannot self-demote", r.status_code == 400, r.status_code)
    r = c.patch(f"/api/admin/users/{uid_a}", headers=ha, json={"delete": True})
    check("admin cannot self-delete", r.status_code == 400, r.status_code)
    db = get_db()
    still = db.execute("SELECT COUNT(*) c FROM users WHERE id=?", [uid_a]).fetchone()["c"]
    db.close()
    check("self-delete left the account intact", still == 1, still)

    # 11. Newly promoted user can now access admin API
    tok_u2 = ba.make_token(uid_u, "Normal User", "user@test.com")
    r = c.get("/api/admin/overview", headers={"Authorization": f"Bearer {tok_u2}"})
    check("promoted user gains admin access", r.status_code == 200, r.status_code)

    # 12. Activity feed
    r = c.get("/api/admin/activity", headers=ha)
    acts = (r.get_json() or {}).get("activity", [])
    check("activity feed populated", len(acts) >= 2, len(acts))
    check("activity entries have user", all("uname" in a for a in acts), acts[:1])

    # 13. Feedback delete
    r = c.delete(f"/api/admin/feedback/{fid}", headers=ha)
    check("admin can delete feedback", r.status_code == 200, r.status_code)
    r = c.get("/api/admin/feedback", headers=ha)
    check("feedback removed", len((r.get_json() or {}).get("feedback", [])) == 0, r.get_json())

    # 14. User deletion
    r = c.patch(f"/api/admin/users/{uid_u}", headers=ha, json={"delete": True})
    check("admin can delete user", r.status_code == 200, r.status_code)
    r = c.get("/api/admin/users", headers=ha)
    check("deleted user gone", len((r.get_json() or {}).get("users", [])) == 1, r.get_json())

    # 15. Secret handling — the signing key is resolved lazily so a value set
    # after import (e.g. from a .env file) is still honoured.
    import models as bm

    old_secret = os.environ.get("SS3_SECRET")
    try:
        os.environ["SS3_SECRET"] = "unit-test-secret"
        check("secret() honours env var", bm.secret() == "unit-test-secret", bm.secret())
        check("is_default_secret() False when set", bm.is_default_secret() is False)
        tok = bm.make_token(uid_a, "Admin Boss", "admin@test.com")
        check("token signed with env secret verifies", bm.verify_token(tok) is not None)
        check(
            "token signed with other secret is rejected",
            bm.verify_token(tok[:-1] + ("0" if tok[-1] != "0" else "1")) is None,
        )
        del os.environ["SS3_SECRET"]
        check("is_default_secret() True when unset", bm.is_default_secret() is True)
    finally:
        if old_secret is None:
            os.environ.pop("SS3_SECRET", None)
        else:
            os.environ["SS3_SECRET"] = old_secret

    # Cleanup
    db = get_db()
    db.execute("DELETE FROM activity_log")
    db.execute("DELETE FROM feedback")
    db.execute("DELETE FROM users")
    db.commit()
    db.close()

    cleanup_db(_TEST_DB)

    failed = [n for n, ok, _ in checks if not ok]
    print("\n" + "=" * 46)
    print(f"{len(checks) - len(failed)}/{len(checks)} checks passed")
    if failed:
        print("FAILED:")
        for n in failed:
            print("  -", n)
        raise SystemExit(1)
    print("ALL ADMIN BACKEND CHECKS PASSED")


if __name__ == "__main__":
    main()

