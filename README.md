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
pip install flask flask-cors
cd backend
python app.py           # http://localhost:5000
```

Then in `frontend/assets/js/core.js` line 3, change:
```js
const USE_MOCK = false;
```

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
│   └── assets/
│       ├── css/
│       │   ├── main.css        Complete design system (dark/light)
│       │   └── graphics.css    Particles, glassmorphism, animations
│       └── js/
│           ├── core.js         Auth, Mock API, PYQ, tests, chatbot, helpers
│           └── sidebar.js      Shared sidebar/topbar injection
│
├── backend/
│   ├── app.py              Flask — all 20+ API routes
│   ├── database.py         SQLite schema + init
│   └── models.py           PBKDF2 password hashing + HMAC JWT
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

## 🔌 API Endpoints (22 routes)

```
POST  /api/auth/register          POST  /api/auth/login
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
```

---

Copyright © Manas Kumar Mishra. All rights reserved.
