# StudySaathi v3 — Your Personalized Learning Companion
> © Manas Kumar Mishra. All rights reserved.

AI-powered EdTech platform for GATE, JEE, NEET, UPSC, CAT, and B.Tech students — with rich graphics, animated UI, and fully offline Mock API.

---

## 🚀 Quick Start (No Backend Needed)

```
1. Open  frontend/index.html  in any modern browser
2. Click "Get Started Free" → Sign up
3. Complete 3-step onboarding (course → semester → exam)
4. All data stored in browser localStorage — works offline
```

---

## ⚙️ Full Stack Setup (Flask)

```bash
pip install flask flask-cors python-dotenv
cd backend
python app.py           # http://localhost:5000
```

Then in `frontend/assets/js/core.js` line 7, change:
```js
const USE_MOCK = false;
```

---

## 🔐 Admin Dashboard (private)

The admin panel lives at `frontend/admin.html` and is only reachable by
accounts with `is_admin = 1`. Non-admins are redirected away automatically.

### Making the first admin

There is no admin signup — the first admin is promoted from the CLI:

```bash
cd backend

# 1. Register normally through the UI (frontend/signup.html), then:
python app.py make-admin you@example.com     # 👑 promotes that account
python app.py list-admins                    # shows current administrators
```

`make-admin` only promotes an account that **already exists** in the
database, so it is safe to run on every deploy.

**Automatic bootstrap (optional).** Set either env var before starting the
server and the matching account is promoted on every boot:

```bash
ADMIN_EMAIL=you@example.com     # promote by email
ADMIN_USER_ID=1                 # …or by user id
```

Both are read by `database.bootstrap_admin()`. If the target account does not
exist yet, the bootstrap is skipped with a warning — it never grants admin to
an unknown account.

### Self-protection (lockout guard)

An admin can never lock themselves out from the panel:

| Action | Own account | Other account |
|---|---|---|
| Demote (`is_admin: false`) | **blocked** (400) | allowed |
| Delete (`delete: true`) | **blocked** (400) | allowed |
| Promote (`is_admin: true`) | no-op | allowed |

The buttons for your own row are also disabled in the UI.

### Admin API routes

```
GET    /api/admin/overview          stats + signups/courses charts + activity
GET    /api/admin/users             ?q=…  ?is_admin=0|1
GET    /api/admin/users/:id         full user record (subjects, activity, …)
PATCH  /api/admin/users/:id         {"is_admin":bool} | {"delete":true}
GET    /api/admin/feedback          ?status=…  ?kind=…  ?q=…
PATCH  /api/admin/feedback/:id      {"status":…, "admin_note":…}
DELETE /api/admin/feedback/:id
GET    /api/admin/activity          platform-wide activity feed
```

All of them require `Authorization: Bearer <token>` **and** `is_admin = 1`
(read live from the database, so revoking access takes effect immediately).
Non-admins get `403`, anonymous callers get `401`.

---

## 🧪 Tests

```bash
cd backend
python3 test_admin.py      # 40 admin API + secret-handling checks
python3 test_contract.py   # 44 response-shape contract checks vs the frontend
python3 test_live.py       # 59 end-to-end HTTP checks against a live server
```

Every suite runs against a **throwaway SQLite file** (see
`backend/test_support.py`), so running the tests never touches your real
development data. Set `SS3_DB_PATH=/path/to.db` to point the server at a
different database file.

`test_live.py` boots the real Flask app on a free port and drives it over
HTTP, including the `make-admin` / `list-admins` CLI commands, so it can be
run safely in parallel with itself.

The frontend has a headless DOM harness:

```bash
mkdir -p /tmp/ss3test && cd /tmp/ss3test && npm install jsdom
node /tmp/ss3test/dom_test.js   # 69 checks across admin.html + feedback.html
```

---

## 🚀 Production launch

The backend reads configuration from the environment, and `backend/.env` is
loaded automatically at startup (via `python-dotenv`).

```bash
# backend/.env
SS3_SECRET=your-long-random-string
SS3_DB_PATH=/var/lib/studysaathi/studysaathi.db
ADMIN_EMAIL=you@example.com
NEVERBOUNCE_API_KEY=your_key
```

```bash
cd backend
python app.py                       # dev server on :5000
```

> ⚠️ **Never deploy without `SS3_SECRET`.** Without it the app falls back to a
> hard-coded development key that is public in the source tree, which lets
> anyone forge auth tokens. The server prints a warning on startup whenever
> the default key is in use.

Generate a strong key with:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

For a real deployment, serve it with a production WSGI server instead of
Flask's dev server:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

And put it behind a reverse proxy (nginx/Caddy) with TLS.

### Environment variables

| Variable | Purpose | Default |
|---|---|---|
| `SS3_SECRET` | HMAC signing key for auth tokens | dev placeholder — **change in prod** |
| `SS3_DB_PATH` | SQLite file location | `database/studysaathi.db` |
| `ADMIN_EMAIL` | Auto-promote this account on boot | unset |
| `ADMIN_USER_ID` | Auto-promote this user id on boot | unset |
| `NEVERBOUNCE_API_KEY` | Email verification API key | unset (verification skipped) |

---

## 📁 Structure

```
SS_v3/
├── frontend/
│   ├── index.html          Landing page (particles, mockup, counters, scroll reveal)
│   ├── dashboard.html      Smart dashboard with glow stat cards
│   ├── subjects.html       Subject + topic manager with AI priority
│   ├── syllabus.html       3-method importer (preloaded/upload/manual)
│   ├── planner.html        5-mode AI study planner
│   ├── pyq.html            PYQ bank with frequency + importance scoring
│   ├── mocktest.html       MCQ tests with timer, score ring, grade
│   ├── analytics.html      Charts, heatmap, streaks, achievements
│   ├── resources.html      Notes, formula sheets, books, videos
│   ├── chatbot.html        Full-page AI study assistant
│   ├── profile.html        Account settings + achievements
│   ├── feedback.html       Feedback form + personal history
│   ├── admin.html          🔐 Private admin dashboard (admin only)
│   └── assets/
│       ├── css/
│       │   ├── main.css        Complete design system (dark/light)
│       │   └── graphics.css    Particles, glassmorphism, animations
│       └── js/
│           ├── core.js         Auth, Mock API, PYQ, tests, chatbot, helpers
│           └── sidebar.js      Shared sidebar/topbar injection
│
├── backend/
│   ├── app.py              Flask — all 30+ API routes
│   ├── database.py         SQLite schema + init + admin bootstrap
│   ├── models.py           PBKDF2 password hashing + HMAC JWT
│   ├── test_support.py     Throwaway-database helper for the test suites
│   ├── test_admin.py       Admin API behaviour tests
│   ├── test_contract.py    Response-shape contract vs the frontend
│   └── test_live.py        End-to-end HTTP tests against a live server
│
├── database/
│   └── studysaathi.db      Auto-created on first run
│
└── README.md
```

---

## ✨ Graphics Features

| Visual | Where |
|---|---|
| Animated particle network (WebGL-style canvas) | index.html |
| Floating dashboard mockup with bar chart | index.html hero |
| Auto-scrolling exam strip (CSS animation) | index.html |
| Scroll-reveal animations (IntersectionObserver) | All sections |
| Count-up number animations | Stats counters |
| Glassmorphism feature cards | Features section |
| Glow bottom-border stat cards (per colour) | All dashboards |
| Animated bar chart (CSS @keyframes growUp) | Dashboard, Analytics |
| 30-day study calendar heatmap | Analytics page |
| SVG score ring with animated stroke | Mock test results |
| Floating accent cards around mockup | Landing hero |
| Dark / Light mode toggle | All pages |

---

## 🌟 Platform Features

| Feature | Detail |
|---|---|
| Smart Dashboard | Glow cards, tasks, exams, streak, weekly chart, AI recs |
| PYQ Bank | Frequency + importance scoring, 4 tabs, subject analytics |
| Mock Test Platform | Timer, navigator, mark-for-review, score ring, grade A–D |
| 5-Mode Study Planner | Balanced / Topper / Crash / Weekend / Working Student |
| Syllabus Importer | Preloaded GATE/JEE/NEET/UPSC/B.Tech + PDF + manual |
| AI Study Assistant | 10 intent categories, quick-action chips, typing indicator |
| Analytics | 30-day heatmap, weekly chart, subject bars, mock trends |
| Resource Hub | 20 curated notes/formula/videos/books/practice sets |
| Achievements | 8 unlockable badges |
| Global Search | Subjects, topics, PYQs, tests — from topbar |
| Dark / Light Mode | Persisted across sessions |

---

## 🔌 API Endpoints (30+ routes)

```
POST  /api/auth/register          POST  /api/auth/login
POST  /api/auth/logout             GET   /api/auth/me
PATCH /api/auth/profile            GET   /api/auth/verify-email
POST  /api/auth/resend-verification
GET   /api/dashboard              GET/POST /api/subjects
POST  /api/subjects/:id/topics    PATCH /api/subjects/topics/:id
GET/POST /api/tasks               PATCH/DELETE /api/tasks/:id
GET/POST /api/exams               DELETE /api/exams/:id
GET/POST /api/progress            GET  /api/analytics
GET/POST /api/pyqs                GET  /api/mocktests
GET  /api/mocktests/:id           POST /api/mocktests/submit
GET  /api/scores                  POST /api/planner/generate
GET  /api/planner/saved           GET  /api/planner/:id
POST /api/chat                    GET  /api/search
GET  /api/achievements            GET  /api/notifications
GET/POST /api/feedback            ── admin routes listed above ──
```

---

Copyright © Manas Kumar Mishra. All rights reserved.
