/**
 * script.js  —  StudySaathi Global JS
 * =====================================
 * Fully offline-capable via localStorage Mock API.
 * Set USE_MOCK = false when Flask backend is running at API_BASE.
 * © Manas Kumar Mishra. All rights reserved.
 */

const API_BASE = "http://localhost:5000/api";
const USE_MOCK = true;

// ── Auth ──────────────────────────────────────────────────────────────────────
const Auth = {
  save(token, user) {
    localStorage.setItem("ss_token", token);
    localStorage.setItem("ss_user", JSON.stringify(user));
  },
  token() {
    return localStorage.getItem("ss_token");
  },
  user() {
    try {
      return JSON.parse(localStorage.getItem("ss_user")) || null;
    } catch {
      return null;
    }
  },
  clear() {
    localStorage.removeItem("ss_token");
    localStorage.removeItem("ss_user");
  },
  isAuth() {
    return !!this.token();
  },
};

// ── LocalStorage DB ───────────────────────────────────────────────────────────
const DB = {
  get(key, def = null) {
    try {
      const v = localStorage.getItem("ss_db_" + key);
      return v !== null ? JSON.parse(v) : def;
    } catch {
      return def;
    }
  },
  set(key, val) {
    localStorage.setItem("ss_db_" + key, JSON.stringify(val));
  },
  uid() {
    return Auth.user()?.id || 0;
  },
};

// ── Date helpers ──────────────────────────────────────────────────────────────
function todayString() {
  return new Date().toISOString().split("T")[0];
}
function daysLeft(dateStr) {
  const t = new Date();
  t.setHours(0, 0, 0, 0);
  return Math.ceil((new Date(dateStr + "T00:00:00") - t) / 86400000);
}
function formatDate(dateStr) {
  if (!dateStr) return "—";
  return new Date(dateStr + "T00:00:00").toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

// ── Colours ───────────────────────────────────────────────────────────────────
const PALETTE = [
  "#3d5af1",
  "#00c9a7",
  "#ec4899",
  "#f5c842",
  "#10b981",
  "#8b5cf6",
];
function subjectColor(i) {
  return PALETTE[i % PALETTE.length];
}

// ── AI Suggestions builder ────────────────────────────────────────────────────
function _buildSuggestions(uid, subs, progress) {
  const suggestions = [];
  const exams = DB.get("exams_" + uid, []).map((e) => ({
    ...e,
    days_left: daysLeft(e.exam_date),
  }));
  subs.forEach((s) => {
    const total = (s.topics || []).length,
      done = (s.topics || []).filter((t) => t.completed).length;
    if (total > 0 && done / total < 0.4)
      suggestions.push({
        type: "weak_subject",
        icon: "📉",
        title: `Focus on ${s.subject_name}`,
        message: `Only ${Math.round((done / total) * 100)}% complete. Spend more time here this week.`,
      });
  });
  const hard = subs.flatMap((s) =>
    (s.topics || [])
      .filter((t) => t.difficulty === "Hard" && !t.completed)
      .map((t) => ({ ...t, subject: s.subject_name })),
  );
  if (hard.length)
    suggestions.push({
      type: "hard_topic",
      icon: "🔴",
      title: `${hard.length} hard topic${hard.length > 1 ? "s" : ""} pending`,
      message: `"${hard[0].topic_name}" (${hard[0].subject}) needs extra attention.`,
    });
  exams
    .filter((e) => e.days_left >= 0 && e.days_left <= 14)
    .forEach((e) =>
      suggestions.push({
        type: "exam_alert",
        icon: "⚠️",
        title: `${e.subject} in ${Math.round(e.days_left)} day${e.days_left !== 1 ? "s" : ""}!`,
        message:
          "Switch to intensive revision mode — past papers + summary notes only.",
      }),
    );
  if (!suggestions.length) {
    const wh = progress
      .filter((p) => (new Date() - new Date(p.date)) / 86400000 <= 7)
      .reduce((s, p) => s + p.hours_studied, 0);
    suggestions.push({
      type: "positive",
      icon: "🌟",
      title:
        wh > 0
          ? `${wh.toFixed(1)}h logged this week`
          : "Welcome to StudySaathi!",
      message:
        wh > 0
          ? "Great consistency! Keep the streak going."
          : "Add subjects, log hours, and get personalised tips here.",
    });
  }
  return suggestions.slice(0, 5);
}

// ── Mock API ───────────────────────────────────────────────────────────────────
const MockAPI = {
  async request(method, path, body) {
    await new Promise((r) => setTimeout(r, 80));
    const uid = DB.uid();

    // Auth
    if (path === "/auth/register" && method === "POST") {
      const users = DB.get("users", []);
      if (users.find((u) => u.email === body.email))
        throw new Error("Email already registered");
      const user = {
        id: Date.now(),
        name: body.name,
        email: body.email,
        password: body.password,
        course: body.course || "",
      };
      users.push(user);
      DB.set("users", users);
      const token = "mock_" + Math.random().toString(36).slice(2);
      return {
        token,
        user: {
          id: user.id,
          name: user.name,
          email: user.email,
          course: user.course,
        },
      };
    }
    if (path === "/auth/login" && method === "POST") {
      const user = DB.get("users", []).find(
        (u) => u.email === body.email && u.password === body.password,
      );
      if (!user) throw new Error("Invalid email or password");
      return {
        token: "mock_" + Math.random().toString(36).slice(2),
        user: {
          id: user.id,
          name: user.name,
          email: user.email,
          course: user.course,
        },
      };
    }
    if (path === "/auth/logout") return { message: "Logged out" };
    if (path === "/auth/me") {
      const u = Auth.user();
      if (!u) throw new Error("Unauthorized");
      return { user: u };
    }

    // Dashboard
    if (path === "/dashboard") {
      const today = todayString(),
        progress = DB.get("progress_" + uid, []),
        subjects = DB.get("subjects_" + uid, []);
      const tasks = DB.get("tasks_" + uid, [])
        .filter((t) => t.date === today)
        .reverse()
        .slice(0, 8);
      const exams = DB.get("exams_" + uid, [])
        .filter((e) => e.exam_date >= today)
        .map((e) => ({ ...e, days_left: daysLeft(e.exam_date) }))
        .sort((a, b) => (a.exam_date > b.exam_date ? 1 : -1))
        .slice(0, 5);
      const todayHrs = progress
        .filter((p) => p.date === today)
        .reduce((s, p) => s + p.hours_studied, 0);
      const allTasks = DB.get("tasks_" + uid, []).filter(
        (t) => t.date === today,
      );
      const allTopics = subjects.flatMap((s) => s.topics || []);
      const studyDates = [...new Set(progress.map((p) => p.date))]
        .sort()
        .reverse();
      let streak = 0;
      for (let i = 0; i < 60; i++) {
        const d = new Date(today);
        d.setDate(d.getDate() - i);
        const ds = d.toISOString().split("T")[0];
        if (studyDates.includes(ds)) streak++;
        else if (i > 0) break;
      }
      return {
        user: Auth.user(),
        date: today,
        tasks,
        exams,
        hours_today: Math.round(todayHrs * 10) / 10,
        tasks_total: allTasks.length,
        tasks_done: allTasks.filter((t) => t.status === "done").length,
        subject_count: subjects.length,
        syllabus_pct: allTopics.length
          ? Math.round(
              (allTopics.filter((t) => t.completed).length / allTopics.length) *
                100,
            )
          : 0,
        streak,
      };
    }

    // Subjects
    if (path === "/subjects/" && method === "GET")
      return { subjects: DB.get("subjects_" + uid, []) };
    if (path === "/subjects/" && method === "POST") {
      const subs = DB.get("subjects_" + uid, []);
      const sub = {
        id: Date.now(),
        user_id: uid,
        subject_name: body.subject_name,
        topics: [],
        created_at: new Date().toISOString(),
      };
      subs.push(sub);
      DB.set("subjects_" + uid, subs);
      return {
        message: "Subject added",
        id: sub.id,
        subject_name: sub.subject_name,
      };
    }
    if (/^\/subjects\/\d+$/.test(path) && method === "DELETE") {
      DB.set(
        "subjects_" + uid,
        DB.get("subjects_" + uid, []).filter(
          (s) => s.id !== parseInt(path.split("/")[2]),
        ),
      );
      return { message: "Subject deleted" };
    }
    if (/^\/subjects\/\d+\/topics$/.test(path) && method === "POST") {
      const sid = parseInt(path.split("/")[2]);
      const subs = DB.get("subjects_" + uid, []);
      const sub = subs.find((s) => s.id === sid);
      if (!sub) throw new Error("Subject not found");
      const topic = {
        id: Date.now(),
        subject_id: sid,
        topic_name: body.topic_name,
        difficulty: body.difficulty || "Medium",
        completed: false,
      };
      (sub.topics = sub.topics || []).push(topic);
      DB.set("subjects_" + uid, subs);
      return { message: "Topic added", ...topic };
    }
    if (/^\/subjects\/topics\/\d+$/.test(path) && method === "PATCH") {
      const tid = parseInt(path.split("/")[3]);
      const subs = DB.get("subjects_" + uid, []);
      for (const s of subs) {
        const t = (s.topics || []).find((t) => t.id === tid);
        if (t) {
          Object.assign(t, body);
          break;
        }
      }
      DB.set("subjects_" + uid, subs);
      return { message: "Topic updated" };
    }
    if (/^\/subjects\/topics\/\d+$/.test(path) && method === "DELETE") {
      const tid = parseInt(path.split("/")[3]);
      const subs = DB.get("subjects_" + uid, []);
      for (const s of subs)
        s.topics = (s.topics || []).filter((t) => t.id !== tid);
      DB.set("subjects_" + uid, subs);
      return { message: "Topic deleted" };
    }

    // Tasks
    if (path.startsWith("/tasks/") && method === "GET") {
      const qs = path.includes("?") ? path.split("?")[1] : "";
      const date = new URLSearchParams(qs).get("date") || todayString();
      return {
        tasks: DB.get("tasks_" + uid, [])
          .filter((t) => t.date === date)
          .reverse(),
        date,
      };
    }
    if (path === "/tasks/" && method === "POST") {
      const tasks = DB.get("tasks_" + uid, []);
      const t = {
        id: Date.now(),
        user_id: uid,
        task: body.task,
        notes: body.notes || "",
        priority: body.priority || "Medium",
        status: "pending",
        date: body.date || todayString(),
      };
      tasks.push(t);
      DB.set("tasks_" + uid, tasks);
      return { message: "Task created", ...t };
    }
    if (/^\/tasks\/\d+$/.test(path) && method === "PATCH") {
      const tid = parseInt(path.split("/")[2]);
      const tasks = DB.get("tasks_" + uid, []);
      const t = tasks.find((t) => t.id === tid);
      if (t) Object.assign(t, body);
      DB.set("tasks_" + uid, tasks);
      return { message: "Task updated" };
    }
    if (/^\/tasks\/\d+$/.test(path) && method === "DELETE") {
      DB.set(
        "tasks_" + uid,
        DB.get("tasks_" + uid, []).filter(
          (t) => t.id !== parseInt(path.split("/")[2]),
        ),
      );
      return { message: "Task deleted" };
    }

    // Exams
    if (path === "/exams/" && method === "GET")
      return {
        exams: DB.get("exams_" + uid, [])
          .map((e) => ({ ...e, days_left: daysLeft(e.exam_date) }))
          .sort((a, b) => (a.exam_date > b.exam_date ? 1 : -1)),
      };
    if (path === "/exams/" && method === "POST") {
      const exams = DB.get("exams_" + uid, []);
      const e = {
        id: Date.now(),
        user_id: uid,
        subject: body.subject,
        exam_date: body.exam_date,
        notes: body.notes || "",
      };
      exams.push(e);
      DB.set("exams_" + uid, exams);
      return { message: "Exam added", ...e };
    }
    if (/^\/exams\/\d+$/.test(path) && method === "DELETE") {
      DB.set(
        "exams_" + uid,
        DB.get("exams_" + uid, []).filter(
          (e) => e.id !== parseInt(path.split("/")[2]),
        ),
      );
      return { message: "Exam deleted" };
    }

    // Progress
    if ((path === "/progress/" || path === "/progress") && method === "GET") {
      const today = todayString(),
        progress = DB.get("progress_" + uid, []),
        subs = DB.get("subjects_" + uid, []);
      const DN = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
      const weekly = [];
      for (let i = 6; i >= 0; i--) {
        const d = new Date();
        d.setDate(d.getDate() - i);
        const ds = d.toISOString().split("T")[0];
        weekly.push({
          label: DN[d.getDay()],
          date: ds,
          hours:
            Math.round(
              progress
                .filter((p) => p.date === ds)
                .reduce((s, p) => s + p.hours_studied, 0) * 10,
            ) / 10,
        });
      }
      const subjMap = {};
      for (const p of progress) {
        const k = p.subject || "Other";
        if (!subjMap[k])
          subjMap[k] = { subject: k, total_hours: 0, days_studied: new Set() };
        subjMap[k].total_hours += p.hours_studied;
        subjMap[k].days_studied.add(p.date);
      }
      const subject_summary = Object.values(subjMap)
        .map((s) => ({
          ...s,
          total_hours: Math.round(s.total_hours * 10) / 10,
          days_studied: s.days_studied.size,
        }))
        .sort((a, b) => b.total_hours - a.total_hours);
      const topic_summary = subs.map((s, i) => {
        const tot = (s.topics || []).length,
          done = (s.topics || []).filter((t) => t.completed).length;
        return {
          subject: s.subject_name,
          total_topics: tot,
          done_topics: done,
          completion_pct: tot ? Math.round((done / tot) * 100) : 0,
          color: PALETTE[i % PALETTE.length],
        };
      });
      const sd = [...new Set(progress.map((p) => p.date))].sort().reverse();
      let streak = 0;
      for (let i = 0; i < 60; i++) {
        const d = new Date(today);
        d.setDate(d.getDate() - i);
        if (sd.includes(d.toISOString().split("T")[0])) streak++;
        else if (i > 0) break;
      }
      return {
        weekly,
        subject_summary,
        topic_summary,
        hours_today:
          Math.round(
            progress
              .filter((p) => p.date === today)
              .reduce((s, p) => s + p.hours_studied, 0) * 10,
          ) / 10,
        streak,
        study_dates: sd,
        suggestions: _buildSuggestions(uid, subs, progress),
      };
    }
    if (path === "/progress/streak" && method === "GET") {
      const progress = DB.get("progress_" + uid, []);
      const sd = [...new Set(progress.map((p) => p.date))].sort().reverse();
      let streak = 0;
      const today = todayString();
      for (let i = 0; i < 60; i++) {
        const d = new Date(today);
        d.setDate(d.getDate() - i);
        if (sd.includes(d.toISOString().split("T")[0])) streak++;
        else if (i > 0) break;
      }
      return { streak, dates: sd.slice(0, 30) };
    }
    if (path === "/progress/suggestions" && method === "GET") {
      return {
        suggestions: _buildSuggestions(
          uid,
          DB.get("subjects_" + uid, []),
          DB.get("progress_" + uid, []),
        ),
      };
    }
    if ((path === "/progress/" || path === "/progress") && method === "POST") {
      const progs = DB.get("progress_" + uid, []);
      const p = {
        id: Date.now(),
        user_id: uid,
        subject: body.subject || "",
        subject_id: body.subject_id || null,
        hours_studied: body.hours_studied,
        notes: body.notes || "",
        date: body.date || todayString(),
      };
      progs.push(p);
      DB.set("progress_" + uid, progs);
      return { message: "Progress logged", ...p };
    }

    // Planner
    if (path === "/planner/generate" && method === "POST") {
      const { exam_date, daily_hours, subjects } = body;
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const examDate = new Date(exam_date + "T00:00:00");
      const dl = Math.max(1, Math.ceil((examDate - today) / 86400000));
      const revDays = Math.max(1, Math.floor(dl * 0.2));
      const studyDays = dl - revDays;
      const ai_suggestions = [];
      if (dl <= 7)
        ai_suggestions.push(
          "🚨 Less than a week left — focus on revision and past papers.",
        );
      if (dl <= 14)
        ai_suggestions.push(
          "⚡ Two weeks to go. Prioritise Hard topics first each day.",
        );
      const hs = subjects.filter((s) => s.difficulty === "Hard");
      if (hs.length)
        ai_suggestions.push(
          `📖 Hard subjects (${hs.map((s) => s.name).join(", ")}) need extra daily time.`,
        );
      ai_suggestions.push(
        "💧 Stay hydrated, take 5-min breaks every 50 minutes.",
      );
      if (!ai_suggestions.length)
        ai_suggestions.push(
          "✅ Great plan! Stick to the schedule and track daily progress.",
        );
      const DN2 = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
      const days = [];
      for (let i = 0; i < Math.min(dl, 60); i++) {
        const d = new Date(today);
        d.setDate(d.getDate() + i);
        const ds = d.toISOString().split("T")[0];
        const isRev = i >= studyDays;
        const label = `${DN2[d.getDay()]}, ${ds}${isRev ? " — Revision Day" : ""}`;
        const slots = [];
        const hrs = Math.min(daily_hours || 6, 10);
        const subjs = subjects.length
          ? subjects
          : [{ name: "General Study", difficulty: "Medium" }];
        if (isRev) {
          slots.push({
            start: "09:00",
            end: "10:30",
            subject: "Revision Session",
            difficulty: null,
            type: "revision",
            tip: "Review all subjects",
          });
          slots.push({
            start: "10:30",
            end: "10:45",
            subject: "Break",
            difficulty: null,
            type: "break",
            tip: "Rest & stretch",
          });
          slots.push({
            start: "10:45",
            end: "12:30",
            subject: "Practice Problems",
            difficulty: null,
            type: "revision",
            tip: "Past year questions",
          });
          slots.push({
            start: "14:00",
            end: "16:00",
            subject: "Mock Test",
            difficulty: null,
            type: "revision",
            tip: "Full-length timed test",
          });
        } else {
          let t = 9;
          for (let j = 0; j < hrs; j++) {
            const subj = subjs[(i * hrs + j) % subjs.length];
            slots.push({
              start: `${String(t).padStart(2, "0")}:00`,
              end: `${String(t + 1).padStart(2, "0")}:00`,
              subject: subj.name,
              difficulty: subj.difficulty || null,
              type: "study",
              tip:
                subj.difficulty === "Hard"
                  ? "Focus deeply — no phone"
                  : subj.difficulty === "Easy"
                    ? "Quick review, move fast"
                    : null,
            });
            t++;
            if (j === 1 && hrs > 3) {
              slots.push({
                start: `${String(t).padStart(2, "0")}:00`,
                end: `${String(t).padStart(2, "0")}:15`,
                subject: "Short Break",
                difficulty: null,
                type: "break",
                tip: "5 min walk",
              });
            }
          }
          slots.push({
            start: `${String(t).padStart(2, "0")}:00`,
            end: `${String(t + 1).padStart(2, "0")}:00`,
            subject: "Daily Review",
            difficulty: null,
            type: "revision",
            tip: "Review today's notes before sleep",
          });
        }
        days.push({ date: ds, day: i + 1, is_revision: isRev, label, slots });
      }
      const plan = {
        id: Date.now(),
        exam_date,
        daily_hours,
        days_left: dl,
        total_study_days: studyDays,
        revision_days: revDays,
        ai_suggestions,
        days,
        created_at: new Date().toISOString(),
      };
      const saved = DB.get("plans_" + uid, []);
      saved.unshift(plan);
      DB.set("plans_" + uid, saved.slice(0, 10));
      return { plan };
    }
    if (
      (path === "/planner/plans" || path === "/planner/saved") &&
      method === "GET"
    )
      return { plans: DB.get("plans_" + uid, []) };
    if (/^\/planner\/plans\/\d+$/.test(path) && method === "GET") {
      const pid = parseInt(path.split("/")[3]);
      const plan = DB.get("plans_" + uid, []).find((p) => p.id === pid);
      if (!plan) throw new Error("Plan not found");
      return { plan: { ...plan, days_left: daysLeft(plan.exam_date) } };
    }

    throw new Error("MockAPI: unknown route " + method + " " + path);
  },
};

// ── Real API ──────────────────────────────────────────────────────────────────
const _RealAPI = {
  async _req(method, path, body = null) {
    const headers = { "Content-Type": "application/json" };
    const token = Auth.token();
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const opts = { method, headers };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(API_BASE + path, opts);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      if (res.status === 401 && !path.includes("/auth/")) {
        Auth.clear();
        window.location.href = "login.html";
        return;
      }
      throw new Error(data.error || `HTTP ${res.status}`);
    }
    return data;
  },
  get(p) {
    return this._req("GET", p);
  },
  post(p, b) {
    return this._req("POST", p, b);
  },
  patch(p, b) {
    return this._req("PATCH", p, b);
  },
  del(p) {
    return this._req("DELETE", p);
  },
};

// ── Unified API ───────────────────────────────────────────────────────────────
const API = {
  get(p) {
    return USE_MOCK ? MockAPI.request("GET", p, null) : _RealAPI.get(p);
  },
  post(p, b) {
    return USE_MOCK ? MockAPI.request("POST", p, b) : _RealAPI.post(p, b);
  },
  patch(p, b) {
    return USE_MOCK ? MockAPI.request("PATCH", p, b) : _RealAPI.patch(p, b);
  },
  del(p) {
    return USE_MOCK ? MockAPI.request("DELETE", p, null) : _RealAPI.del(p);
  },
};

// ── Toast ─────────────────────────────────────────────────────────────────────
function showToast(msg, type = "success") {
  let t = document.getElementById("global-toast");
  if (!t) {
    t = document.createElement("div");
    t.id = "global-toast";
    t.className = "toast";
    document.body.appendChild(t);
  }
  const icons = { success: "✓", error: "✕", info: "ℹ" };
  t.className = `toast ${type}`;
  t.innerHTML = `<span>${icons[type] || "✓"}</span> ${msg}`;
  t.classList.add("show");
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.classList.remove("show"), 3200);
}

// ── Loading spinner ───────────────────────────────────────────────────────────
function setLoading(btn, isLoading) {
  if (!btn) return;
  if (isLoading) {
    btn._origText = btn.innerHTML;
    btn.innerHTML = `<span class="spinner"></span> Please wait…`;
    btn.disabled = true;
  } else {
    btn.innerHTML = btn._origText || btn.innerHTML;
    btn.disabled = false;
  }
}

// ── Guards ────────────────────────────────────────────────────────────────────
function requireAuth() {
  if (!Auth.isAuth()) {
    window.location.href = "login.html";
    return false;
  }
  return true;
}
function redirectIfAuth() {
  if (Auth.isAuth()) window.location.href = "dashboard.html";
}

// ── Badge helpers ─────────────────────────────────────────────────────────────
function badgeHTML(value, map) {
  return `<span class="badge ${map[value] || "badge-medium"}">${value}</span>`;
}
const PRIORITY_MAP = {
  High: "badge-high",
  Medium: "badge-medium",
  Low: "badge-low",
};
const DIFFICULTY_MAP = {
  Hard: "badge-hard",
  Medium: "badge-medium",
  Easy: "badge-easy",
};
const STATUS_MAP = { done: "badge-done", pending: "badge-pending" };

// ── UI helpers ────────────────────────────────────────────────────────────────
function emptyState(icon, msg) {
  return `<div class="empty-state"><div class="es-icon">${icon}</div><p>${msg}</p></div>`;
}
function loadingRow() {
  return `<div class="loading-row"><div class="spinner"></div> Loading…</div>`;
}
function openModal(id) {
  document.getElementById(id)?.classList.add("open");
}
function closeModal(id) {
  document.getElementById(id)?.classList.remove("open");
}
document.addEventListener("click", (e) => {
  if (e.target.classList.contains("modal-overlay"))
    e.target.classList.remove("open");
});

// ── Nav / user ────────────────────────────────────────────────────────────────
function populateUserNav() {
  const u = Auth.user();
  if (!u) return;
  const el = document.getElementById("nav-user-name");
  if (el) el.textContent = u.name?.split(" ")[0] || "User";
}
async function logout() {
  try {
    await API.post("/auth/logout");
  } catch (_) {}
  Auth.clear();
  window.location.href = "index.html";
}

// ── Chart helpers ─────────────────────────────────────────────────────────────
function progressBarHTML(subject, pct, color) {
  return `<div class="prog-item"><div class="prog-header"><span>${subject}</span><span class="prog-pct">${pct}%</span></div><div class="prog-bar"><div class="prog-fill" style="width:${pct}%;background:${color}"></div></div></div>`;
}
function buildBarChart(containerId, data, maxVal) {
  const wrap = document.getElementById(containerId);
  if (!wrap) return;
  const max = maxVal || Math.max(...data.map((d) => d.value), 1);
  wrap.innerHTML = data
    .map((d) => {
      const h = Math.max(3, Math.round((d.value / max) * 120));
      return `<div class="bar-col"><div class="bar-val">${d.value}h</div><div class="bar" style="height:${h}px;background:${d.color || "var(--indigo)"}"></div><div class="bar-label">${d.label}</div></div>`;
    })
    .join("");
}
function buildStreakRow(containerId, activeDates, count) {
  const wrap = document.getElementById(containerId);
  if (!wrap) return;
  const days = ["M", "T", "W", "T", "F", "S", "S"],
    today = new Date(),
    ts = todayString();
  let html = "";
  for (let i = 6; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    const ds = d.toISOString().split("T")[0],
      lbl = days[d.getDay() === 0 ? 6 : d.getDay() - 1],
      cls = ds === ts ? "today" : activeDates.includes(ds) ? "done" : "";
    html += `<div class="streak-day ${cls}" title="${ds}">${lbl}</div>`;
  }
  wrap.innerHTML = html;
  const ce = document.getElementById("streak-count");
  if (ce) ce.textContent = count;
}

document.addEventListener("DOMContentLoaded", () => {
  populateUserNav();
});
