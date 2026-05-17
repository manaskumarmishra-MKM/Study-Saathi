# 📚 StudySaathi – AI-Powered Study Planner

> **Plan Better. Study Smarter.**
> © Manas Kumar Mishra. All rights reserved.

---

## 🗂 Project Structure

```
studysaathi/
├── backend/
│   ├── app.py              ← Flask entry point (run this)
│   ├── database.py         ← SQLite setup & table creation
│   ├── models.py           ← Password hashing, token auth
│   ├── requirements.txt    ← Python dependencies
│   └── routes/
│       ├── auth.py         ← Register, Login, Logout, Me
│       ├── subjects.py     ← Subjects & Topics CRUD
│       ├── planner.py      ← Plan generation algorithm
│       ├── tasks.py        ← Daily tasks CRUD
│       ├── exams.py        ← Exam countdown management
│       └── progress.py     ← Study hours logging & stats
├── frontend/
│   ├── index.html          ← Landing page
│   ├── login.html          ← Login & Signup
│   ├── dashboard.html      ← Main dashboard
│   ├── planner.html        ← Subject setup + plan generator
│   ├── progress.html       ← Progress tracker & charts
│   ├── profile.html        ← Profile & settings
│   ├── styles.css          ← Global dark-theme stylesheet
│   └── script.js           ← API client + shared utilities
└── README.md
```

---

## ⚙️ Tech Stack

| Layer      | Technology                          |
|------------|-------------------------------------|
| Frontend   | HTML5, CSS3, Vanilla JavaScript     |
| Backend    | Python 3.10+ · Flask                |
| Database   | SQLite (via Python's built-in sqlite3) |
| Auth       | Token-based (SHA-256 salted hash)   |
| AI Logic   | Rule-based suggestion engine        |

---

## 🚀 Setup & Run

### 1. Prerequisites
```
Python 3.10 or higher
Flask (pip install flask)
A web browser
```

### 2. Install dependencies
```bash
cd studysaathi/backend
pip install flask
```

### 3. Start the backend
```bash
cd studysaathi/backend
python app.py
```
Server runs at: **http://localhost:5000**

The SQLite database (`studysaathi.db`) is created automatically on first run.

### 4. Open the frontend
Open `studysaathi/frontend/index.html` in your browser.
- You can use any local server, e.g.:
  ```bash
  cd studysaathi/frontend
  python -m http.server 3000
  ```
  Then visit: **http://localhost:3000**

> ⚠️ Make sure the backend is running before opening the frontend.

---

## 🔗 API Endpoints

### Auth
| Method | Endpoint            | Description           |
|--------|---------------------|-----------------------|
| POST   | /api/auth/register  | Create account        |
| POST   | /api/auth/login     | Login, get token      |
| POST   | /api/auth/logout    | Invalidate token      |
| GET    | /api/auth/me        | Get current user      |

### Subjects & Topics
| Method | Endpoint                         | Description           |
|--------|----------------------------------|-----------------------|
| GET    | /api/subjects/                   | List subjects+topics  |
| POST   | /api/subjects/                   | Add subject           |
| DELETE | /api/subjects/<id>               | Delete subject        |
| POST   | /api/subjects/<id>/topics        | Add topic             |
| PATCH  | /api/subjects/topics/<id>        | Toggle complete       |
| DELETE | /api/subjects/topics/<id>        | Delete topic          |

### Planner
| Method | Endpoint               | Description              |
|--------|------------------------|--------------------------|
| POST   | /api/planner/generate  | Generate study plan      |
| GET    | /api/planner/plans     | List saved plans         |
| GET    | /api/planner/plans/<id>| Get specific plan        |

### Tasks
| Method | Endpoint          | Description        |
|--------|-------------------|--------------------|
| GET    | /api/tasks/       | List tasks by date |
| POST   | /api/tasks/       | Create task        |
| PATCH  | /api/tasks/<id>   | Update task        |
| DELETE | /api/tasks/<id>   | Delete task        |

### Exams
| Method | Endpoint          | Description     |
|--------|-------------------|-----------------|
| GET    | /api/exams/       | List exams      |
| POST   | /api/exams/       | Add exam        |
| DELETE | /api/exams/<id>   | Delete exam     |

### Progress
| Method | Endpoint                    | Description           |
|--------|-----------------------------|-----------------------|
| POST   | /api/progress/              | Log study session     |
| GET    | /api/progress/              | Get weekly summary    |
| GET    | /api/progress/streak        | Get study streak      |
| GET    | /api/progress/suggestions   | AI suggestions        |

### Dashboard
| Method | Endpoint       | Description              |
|--------|----------------|--------------------------|
| GET    | /api/dashboard | Full dashboard aggregate |

---

## 🧠 AI Suggestion Logic

The suggestion engine (`routes/progress.py`) works on these rules:

1. **Weak Subject** — subject with fewest logged hours gets flagged
2. **Hard Pending Topics** — incomplete Hard-difficulty topics surface as urgent
3. **Exam Alerts** — exams within 14 days trigger revision-mode alerts
4. **Positive Feedback** — if nothing urgent, shows encouragement

---

## 📊 Database Schema

```sql
users       (id, name, email, password, course, created_at)
tokens      (token, user_id, created_at)
subjects    (id, user_id, subject_name, created_at)
topics      (id, subject_id, topic_name, difficulty, completed)
tasks       (id, user_id, task, notes, status, priority, date)
exams       (id, user_id, subject, exam_date, notes, created_at)
progress    (id, user_id, subject, hours_studied, date)
study_plans (id, user_id, exam_date, daily_hours, plan_json, created_at)
```

---

## 🎯 Demo Flow (Hackathon Walkthrough)

1. Open `index.html` → landing page
2. Click **Get Started** → signup form
3. Register with name, email, password, course
4. Redirected to **Dashboard** automatically
5. Go to **Planner** → Add subjects (e.g. Mathematics, Physics)
6. Add topics with difficulty levels
7. Click **Generate Plan** → enter exam date + hours → see timetable
8. Back to **Dashboard** → Add tasks + exams
9. Log study hours via Quick Log or sidebar
10. Visit **Progress** → see charts, streak, AI suggestions
11. Visit **Profile** → manage settings

---

## 🔐 Security Notes

- Passwords stored as `salt:sha256(salt+password)` — never plaintext
- Tokens are 64-char random hex strings with 7-day expiry
- Foreign keys enforced at DB level
- All protected routes validate token on every request

---

## 🏁 Footer

> **© Manas Kumar Mishra. All rights reserved.**
> StudySaathi – Plan Better. Study Smarter.

---

## ✅ Frontend (No Backend Required)

The frontend now works **fully offline** using a localStorage Mock API.

**To open directly in browser:**
```
Open frontend/index.html in any modern browser
```
No server needed. All data is stored in your browser's localStorage.

**To switch to real Flask backend:**
1. Run `python backend/app.py`
2. In `frontend/script.js`, set `const USE_MOCK = false;`

