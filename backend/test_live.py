"""End-to-end test of the real backend over HTTP (no mocking).

Starts the Flask app in a background thread, then exercises the exact
request sequence the frontend pages perform.

Run:  python3 test_live.py

The suite runs against a throwaway database so the real dev data is untouched.
"""

import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

from test_support import cleanup_db, isolate_db

_TEST_DB = isolate_db("ss3_live_")

import app as ba  # noqa: E402  (must import after the DB path is set)
from database import get_db, init_db  # noqa: E402

BASE = "http://127.0.0.1:{port}/api"
BACKEND = "/Users/manaskumarmishra/Downloads/SS_v3/backend"


def _free_port():
    """Ask the OS for an unused port so parallel test runs never clash."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


PORT = _free_port()

problems = []


def check(name, cond, extra=""):
    print(("OK   " if cond else "FAIL ") + name + ("" if cond else f"  <- {extra}"))
    if not cond:
        problems.append(name)


def call(method, path, body=None, token=None):
    req = urllib.request.Request(
        BASE.format(port=PORT) + path,
        data=json.dumps(body).encode() if body is not None else None,
        method=method,
        headers={
            "Content-Type": "application/json",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"raw": raw}


def seed():
    init_db()
    db = get_db()
    for t in ("activity_log", "feedback", "users"):
        db.execute(f"DELETE FROM {t}")
    db.commit()
    db.close()
    pw = ba.hash_pw("x")
    for email, name, admin in (
        ("admin@test.com", "Admin Boss", 1),
        ("user@test.com", "Normal User", 0),
        ("cli@test.com", "CLI Tester", 0),
    ):
        db = get_db()
        db.execute(
            "INSERT INTO users(name, email, password, course, semester, exam, is_admin) "
            "VALUES(?, ?, ?, 'btech-cse', 3, 'GATE', ?)",
            [name, email, pw, admin],
        )
        db.commit()
        db.close()


def main():
    seed()
    threading.Thread(
        target=lambda: ba.app.run(
            host="127.0.0.1", port=PORT, debug=False, use_reloader=False
        ),
        daemon=True,
    ).start()
    # Wait for the server to accept connections before firing requests.
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", PORT), timeout=0.5):
                break
        except OSError:
            time.sleep(0.1)

    # ---- Logins ----
    st, d = call("POST", "/auth/login", {"email": "admin@test.com", "password": "x"})
    check("admin login", st == 200 and "token" in d, (st, d))
    atok = d.get("token")
    st, d = call("POST", "/auth/login", {"email": "user@test.com", "password": "x"})
    check("user login", st == 200 and "token" in d, (st, d))
    utok = d.get("token")

    # ---- Overview ----
    st, d = call("GET", "/admin/overview", token=atok)
    check("overview loads", st == 200, (st, d))
    check("overview stats present", "stats" in d and d["stats"]["total_users"] == 3, d.get("stats"))
    check("overview has signups series", isinstance(d.get("signups"), list), type(d.get("signups")))
    check("overview has courses", isinstance(d.get("courses"), list), type(d.get("courses")))
    check("overview has activity", isinstance(d.get("activity"), list), type(d.get("activity")))
    check("overview has feedback_kinds", isinstance(d.get("feedback_kinds"), list), type(d.get("feedback_kinds")))

    # ---- Users ----
    st, d = call("GET", "/admin/users", token=atok)
    check("users list loads", st == 200 and len(d.get("users", [])) == 3, (st, d))
    u = d["users"][0]
    for k in ("id", "name", "email", "course", "is_admin", "created_at", "c_subjects", "c_hours"):
        check(f"user row has {k}", k in u, sorted(u.keys()))
    st, d = call("GET", "/admin/users?q=Normal", token=atok)
    check("user search works", st == 200 and len(d.get("users", [])) == 1, (st, d))
    st, d = call("GET", "/admin/users?is_admin=1", token=atok)
    check("admin-only filter works", st == 200 and len(d.get("users", [])) == 1, (st, d))
    admin_id = d["users"][0]["id"]

    # ---- User detail modal ----
    st, d = call("GET", f"/admin/users/{admin_id}", token=atok)
    check("user detail loads", st == 200 and "user" in d, (st, d))
    for k in ("subjects", "topics", "progress", "scores", "feedback", "activity"):
        check(f"user detail has {k}", k in d, sorted(d.keys()))

    # ---- Feedback submit ----
    st, d = call(
        "POST",
        "/feedback",
        {"kind": "review", "rating": 5, "title": "Great", "message": "Love it"},
        token=utok,
    )
    check("user submits feedback", st in (200, 201), (st, d))
    st, d = call("POST", "/feedback", {"kind": "bug", "message": ""}, token=utok)
    check("empty feedback rejected", st == 400, (st, d))

    # ---- Feedback visibility ----
    st, d = call("GET", "/feedback", token=utok)
    check("user sees own feedback", st == 200 and len(d.get("feedback", [])) == 1, (st, d))
    st, d = call("GET", "/admin/feedback", token=atok)
    check("admin sees all feedback", st == 200 and len(d.get("feedback", [])) == 1, (st, d))
    fid = d["feedback"][0]["id"]
    check("feedback row has uname", "uname" in d["feedback"][0], sorted(d["feedback"][0].keys()))

    # ---- Admin handles feedback ----
    st, d = call(
        "PATCH",
        f"/admin/feedback/{fid}",
        {"status": "resolved", "admin_note": "Shipped in v3.2"},
        token=atok,
    )
    check("feedback updated", st == 200 and d["feedback"]["status"] == "resolved", (st, d))
    check("admin note stored", d["feedback"]["admin_note"] == "Shipped in v3.2", d["feedback"])

    # ---- User sees the admin note ----
    st, d = call("GET", "/feedback", token=utok)
    check("user sees admin note", d["feedback"][0]["admin_note"] == "Shipped in v3.2", d["feedback"][0])
    check("user sees updated status", d["feedback"][0]["status"] == "resolved", d["feedback"][0])

    # ---- Filters ----
    st, d = call("GET", "/admin/feedback?status=resolved", token=atok)
    check("status filter matches", st == 200 and len(d["feedback"]) == 1, (st, d))
    st, d = call("GET", "/admin/feedback?status=new", token=atok)
    check("status filter excludes", st == 200 and len(d["feedback"]) == 0, (st, d))
    st, d = call("GET", "/admin/feedback?kind=review", token=atok)
    check("kind filter matches", st == 200 and len(d["feedback"]) == 1, (st, d))

    # ---- Activity ----
    st, d = call("GET", "/admin/activity", token=atok)
    check("activity feed loads", st == 200 and len(d.get("activity", [])) >= 2, (st, d))
    check("activity entries carry uname", all("uname" in a for a in d["activity"]), d["activity"][:1])

    # ---- Authorisation ----
    for ep in ("/admin/overview", "/admin/users", "/admin/feedback", "/admin/activity"):
        st, d = call("GET", ep, token=utok)
        check(f"non-admin blocked from {ep}", st == 403, (st, d))
    st, d = call("GET", "/admin/overview")
    check("anonymous blocked from overview", st == 401, (st, d))

    # ---- Promote / demote ----
    st, d = call("GET", "/admin/users", token=atok)
    other = [x for x in d["users"] if x["email"] == "user@test.com"][0]
    st, d = call("PATCH", f"/admin/users/{other['id']}", {"is_admin": True}, token=atok)
    check("promote works", st == 200 and d["user"]["is_admin"] == 1, (st, d))
    st, d = call("GET", "/admin/overview", token=utok)
    check("promoted user gains access", st == 200, (st, d))
    st, d = call("PATCH", f"/admin/users/{other['id']}", {"is_admin": False}, token=atok)
    check("demote works", st == 200 and d["user"]["is_admin"] == 0, (st, d))
    st, d = call("GET", "/admin/overview", token=utok)
    check("demoted user loses access", st == 403, (st, d))

    # ---- Self-protection ----
    st, d = call("PATCH", f"/admin/users/{admin_id}", {"is_admin": False}, token=atok)
    check("self-demote blocked", st == 400, (st, d))
    st, d = call("PATCH", f"/admin/users/{admin_id}", {"delete": True}, token=atok)
    check("self-delete blocked", st == 400, (st, d))
    st, d = call("GET", "/admin/users", token=atok)
    check("self-delete left admin account intact", any(x["id"] == admin_id for x in d["users"]), d)

    # ---- Delete feedback + user ----
    st, d = call("DELETE", f"/admin/feedback/{fid}", token=atok)
    check("feedback deleted", st == 200, (st, d))
    st, d = call("GET", "/admin/feedback", token=atok)
    check("feedback gone", len(d.get("feedback", [])) == 0, d)
    st, d = call("PATCH", f"/admin/users/{other['id']}", {"delete": True}, token=atok)
    check("user deleted", st == 200, (st, d))
    st, d = call("GET", "/admin/users", token=atok)
    check("deleted user gone", len(d.get("users", [])) == 2, d)

    # ---- CLI ----
    env = {**os.environ, "SS3_DB_PATH": _TEST_DB}
    res = subprocess.run(
        [sys.executable, "app.py", "list-admins"],
        cwd=BACKEND, capture_output=True, text=True, env=env,
    )
    check("CLI list-admins works", "admin@test.com" in res.stdout, res.stdout + res.stderr)
    res = subprocess.run(
        [sys.executable, "app.py", "make-admin", "cli@test.com"],
        cwd=BACKEND, capture_output=True, text=True, env=env,
    )
    check("CLI make-admin works", "administrator" in res.stdout, res.stdout + res.stderr)
    res = subprocess.run(
        [sys.executable, "app.py", "list-admins"],
        cwd=BACKEND, capture_output=True, text=True, env=env,
    )
    check("CLI list shows new admin", "cli@test.com" in res.stdout, res.stdout)

    cleanup_db(_TEST_DB)

    print()
    if problems:
        print(f"{len(problems)} PROBLEM(S): {problems}")
        return 1
    print("ALL LIVE BACKEND E2E CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
