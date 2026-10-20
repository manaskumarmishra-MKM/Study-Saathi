/**
 * core.js — StudySaathi v3 Shared Engine
 * © Manas Kumar Mishra. All rights reserved.
 */
"use strict";
const API_BASE = "http://localhost:5000/api",
  USE_MOCK = true;
const Auth = {
  save(t, u) {
    localStorage.setItem("ss3_token", t);
    localStorage.setItem("ss3_user", JSON.stringify(u));
  },
  token() {
    return localStorage.getItem("ss3_token");
  },
  user() {
    try {
      return JSON.parse(localStorage.getItem("ss3_user"));
    } catch {
      return null;
    }
  },
  clear() {
    localStorage.removeItem("ss3_token");
    localStorage.removeItem("ss3_user");
  },
  isAuth() {
    return !!this.token();
  },
};
const DB = {
  get(k, d = null) {
    try {
      const v = localStorage.getItem("ss3_" + k);
      return v !== null ? JSON.parse(v) : d;
    } catch {
      return d;
    }
  },
  set(k, v) {
    localStorage.setItem("ss3_" + k, JSON.stringify(v));
  },
  uid() {
    return Auth.user()?.id || 0;
  },
};
const todayStr = () => new Date().toISOString().split("T")[0];
const daysLeft = (ds) => {
  const t = new Date();
  t.setHours(0, 0, 0, 0);
  return Math.ceil((new Date(ds + "T00:00:00") - t) / 86400000);
};
const fmtDate = (ds) => {
  if (!ds) return "—";
  return new Date(ds + "T00:00:00").toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
};
const PALETTE = [
  "#3d5af1",
  "#00c9a7",
  "#ec4899",
  "#f5c842",
  "#10b981",
  "#8b5cf6",
  "#f97316",
  "#ef4444",
];

const COURSES = {
  "btech-cse": {
    name: "B.Tech CSE",
    subjects: {
      1: [
        "Engineering Mathematics I",
        "Engineering Physics",
        "Programming in C",
        "Basic Electronics",
        "English Communication",
      ],
      2: [
        "Engineering Mathematics II",
        "Data Structures",
        "Digital Logic",
        "Electrical Engineering",
        "Environmental Science",
      ],
      3: [
        "Algorithms",
        "OOP with Java",
        "Discrete Mathematics",
        "Computer Organization",
        "Software Engineering",
      ],
      4: [
        "DBMS",
        "Operating Systems",
        "Computer Networks",
        "Theory of Computation",
        "Microprocessors",
      ],
      5: [
        "Compiler Design",
        "Artificial Intelligence",
        "Web Technology",
        "Elective I",
        "Project I",
      ],
      6: [
        "Machine Learning",
        "Cloud Computing",
        "Information Security",
        "Elective II",
        "Project II",
      ],
      7: [
        "Big Data Analytics",
        "Mobile Computing",
        "Elective III",
        "Minor Project",
      ],
      8: ["Major Project", "Seminar", "Industrial Training"],
    },
  },
  "btech-ece": {
    name: "B.Tech ECE",
    subjects: {
      1: [
        "Engineering Mathematics I",
        "Engineering Physics",
        "Basic Electronics",
        "Programming",
        "English",
      ],
      2: [
        "Engineering Mathematics II",
        "Signals & Systems",
        "Analog Circuits",
        "Digital Electronics",
        "EMT",
      ],
      3: [
        "Network Analysis",
        "Electronic Devices",
        "Control Systems",
        "Communication Theory",
        "VLSI",
      ],
      4: [
        "Microprocessors",
        "Digital Signal Processing",
        "Antenna Theory",
        "RF Engineering",
        "Embedded Systems",
      ],
    },
  },
  gate: {
    name: "GATE CS",
    subjects: {
      1: [
        "Discrete Mathematics",
        "Algorithms",
        "Data Structures",
        "Operating Systems",
        "DBMS",
        "Computer Networks",
        "Theory of Computation",
        "Digital Logic",
        "Computer Organization",
        "Compiler Design",
        "Engineering Mathematics",
        "General Aptitude",
      ],
    },
  },
  jee: {
    name: "JEE Advanced",
    subjects: {
      1: [
        "Physics – Mechanics",
        "Physics – Thermodynamics",
        "Physics – Electrostatics",
        "Physics – Modern Physics",
        "Chemistry – Organic",
        "Chemistry – Inorganic",
        "Chemistry – Physical",
        "Mathematics – Calculus",
        "Mathematics – Algebra",
        "Mathematics – Coordinate Geometry",
      ],
    },
  },
  neet: {
    name: "NEET",
    subjects: {
      1: [
        "Physics – Mechanics",
        "Physics – Optics",
        "Biology – Zoology",
        "Biology – Botany",
        "Chemistry – Organic",
        "Chemistry – Inorganic",
        "Chemistry – Physical",
      ],
    },
  },
  upsc: {
    name: "UPSC CSE",
    subjects: {
      1: [
        "History",
        "Geography",
        "Polity",
        "Economics",
        "Science & Tech",
        "Environment",
        "Current Affairs",
        "Essay",
        "Ethics & Integrity",
        "Optional Subject",
      ],
    },
  },
  cat: {
    name: "CAT",
    subjects: {
      1: [
        "Quantitative Aptitude",
        "Verbal Ability",
        "Logical Reasoning",
        "Data Interpretation",
      ],
    },
  },
};

const PRI_MAP = {
  Algorithms: "High",
  "Data Structures": "High",
  DBMS: "High",
  "Operating Systems": "High",
  "Computer Networks": "High",
  "Discrete Mathematics": "High",
  TOC: "Medium",
  "Compiler Design": "Medium",
  Polity: "High",
  Mechanics: "High",
  Optics: "High",
  Calculus: "High",
  "Organic Chemistry": "High",
  Algebra: "Medium",
  Thermodynamics: "Medium",
  Geography: "Medium",
  Electronics: "Low",
  English: "Low",
};
function getTopicPriority(t) {
  const k = Object.keys(PRI_MAP).find((k) =>
    t.toLowerCase().includes(k.toLowerCase()),
  );
  return k ? PRI_MAP[k] : "Medium";
}

const PYQ_SEED = [
  {
    id: 1,
    subject: "Algorithms",
    exam: "GATE",
    year: 2023,
    unit: "Graph Algorithms",
    question:
      "What is the time complexity of Dijkstra's algorithm using a min-heap?",
    answer: "O((V+E) log V)",
    difficulty: "Hard",
    frequency: 6,
    importance: 95,
  },
  {
    id: 2,
    subject: "Algorithms",
    exam: "GATE",
    year: 2022,
    unit: "Sorting",
    question: "Which sorting algorithm is stable and O(n log n) worst-case?",
    answer: "Merge Sort",
    difficulty: "Medium",
    frequency: 5,
    importance: 88,
  },
  {
    id: 3,
    subject: "Algorithms",
    exam: "GATE",
    year: 2021,
    unit: "Searching",
    question: "Time complexity of binary search on n elements is:",
    answer: "O(log n)",
    difficulty: "Easy",
    frequency: 7,
    importance: 92,
  },
  {
    id: 4,
    subject: "Operating Systems",
    exam: "GATE",
    year: 2023,
    unit: "Memory Management",
    question:
      "Belady's Anomaly is observed in which page replacement algorithm?",
    answer: "FIFO",
    difficulty: "Medium",
    frequency: 5,
    importance: 85,
  },
  {
    id: 5,
    subject: "Operating Systems",
    exam: "GATE",
    year: 2022,
    unit: "Scheduling",
    question: "Which CPU scheduling algorithm can lead to starvation?",
    answer: "Priority Scheduling",
    difficulty: "Easy",
    frequency: 6,
    importance: 87,
  },
  {
    id: 6,
    subject: "DBMS",
    exam: "GATE",
    year: 2023,
    unit: "Normalization",
    question:
      "Which normal form eliminates transitive functional dependencies?",
    answer: "Third Normal Form (3NF)",
    difficulty: "Medium",
    frequency: 8,
    importance: 96,
  },
  {
    id: 7,
    subject: "DBMS",
    exam: "GATE",
    year: 2022,
    unit: "Transactions",
    question: "ACID properties — what does 'I' stand for?",
    answer: "Isolation",
    difficulty: "Easy",
    frequency: 5,
    importance: 83,
  },
  {
    id: 8,
    subject: "Computer Networks",
    exam: "GATE",
    year: 2023,
    unit: "OSI Model",
    question: "Which OSI layer handles logical addressing?",
    answer: "Network Layer (Layer 3)",
    difficulty: "Easy",
    frequency: 7,
    importance: 91,
  },
  {
    id: 9,
    subject: "Computer Networks",
    exam: "GATE",
    year: 2022,
    unit: "TCP/IP",
    question: "TCP connection establishment uses how many handshakes?",
    answer: "3 (Three-way handshake)",
    difficulty: "Easy",
    frequency: 6,
    importance: 89,
  },
  {
    id: 10,
    subject: "Discrete Mathematics",
    exam: "GATE",
    year: 2023,
    unit: "Graph Theory",
    question: "A complete graph with n vertices has how many edges?",
    answer: "n(n-1)/2",
    difficulty: "Medium",
    frequency: 5,
    importance: 82,
  },
  {
    id: 11,
    subject: "Engineering Physics",
    exam: "University",
    year: 2023,
    unit: "Quantum Mechanics",
    question: "State Heisenberg's Uncertainty Principle.",
    answer: "Δx · Δp ≥ ℏ/2",
    difficulty: "Medium",
    frequency: 4,
    importance: 78,
  },
  {
    id: 12,
    subject: "Engineering Mathematics I",
    exam: "University",
    year: 2023,
    unit: "Laplace Transforms",
    question: "Laplace transform of sin(at) is:",
    answer: "a/(s²+a²)",
    difficulty: "Medium",
    frequency: 4,
    importance: 76,
  },
  {
    id: 13,
    subject: "Chemistry – Organic",
    exam: "JEE",
    year: 2023,
    unit: "Oxidation",
    question:
      "Which reagent oxidises primary alcohol to aldehyde without over-oxidation?",
    answer: "PCC (Pyridinium Chlorochromate)",
    difficulty: "Hard",
    frequency: 4,
    importance: 80,
  },
  {
    id: 14,
    subject: "Physics – Mechanics",
    exam: "JEE",
    year: 2023,
    unit: "Projectile Motion",
    question: "For maximum range, projectile is launched at angle:",
    answer: "45°",
    difficulty: "Easy",
    frequency: 5,
    importance: 84,
  },
  {
    id: 15,
    subject: "Mathematics – Calculus",
    exam: "JEE",
    year: 2022,
    unit: "Differentiation",
    question: "Derivative of xⁿ is:",
    answer: "n·xⁿ⁻¹",
    difficulty: "Easy",
    frequency: 6,
    importance: 87,
  },
  {
    id: 16,
    subject: "History",
    exam: "UPSC",
    year: 2023,
    unit: "Freedom Struggle",
    question: "Non-Cooperation Movement was launched in which year?",
    answer: "1920",
    difficulty: "Easy",
    frequency: 5,
    importance: 83,
  },
  {
    id: 17,
    subject: "Polity",
    exam: "UPSC",
    year: 2023,
    unit: "Fundamental Rights",
    question: "Article 32 of the Indian Constitution deals with:",
    answer: "Right to Constitutional Remedies",
    difficulty: "Medium",
    frequency: 7,
    importance: 93,
  },
  {
    id: 18,
    subject: "Geography",
    exam: "UPSC",
    year: 2022,
    unit: "Physical Geography",
    question: "Ganga originates from:",
    answer: "Gangotri Glacier",
    difficulty: "Easy",
    frequency: 4,
    importance: 75,
  },
];

const TEST_SEED = [
  {
    id: 1,
    title: "GATE CS — Full Mock 1",
    subject: "GATE CS",
    duration: 180,
    total_marks: 100,
    questions: [
      {
        id: 1,
        text: "Which data structure uses LIFO?",
        opts: ["Queue", "Stack", "Tree", "Graph"],
        correct: 1,
        subj: "Data Structures",
        marks: 2,
      },
      {
        id: 2,
        text: "Worst-case time complexity of QuickSort?",
        opts: ["O(n log n)", "O(n²)", "O(n)", "O(log n)"],
        correct: 1,
        subj: "Algorithms",
        marks: 2,
      },
      {
        id: 3,
        text: "Which is NOT a valid SQL command?",
        opts: ["SELECT", "UPDATE", "REMOVE", "DELETE"],
        correct: 2,
        subj: "DBMS",
        marks: 2,
      },
      {
        id: 4,
        text: "TCP is a ________ protocol.",
        opts: [
          "Connectionless",
          "Connection-oriented",
          "Broadcast",
          "Multicast",
        ],
        correct: 1,
        subj: "Networks",
        marks: 2,
      },
      {
        id: 5,
        text: "Which traversal visits BST in ascending order?",
        opts: ["Preorder", "Postorder", "Inorder", "Level-order"],
        correct: 2,
        subj: "Data Structures",
        marks: 2,
      },
      {
        id: 6,
        text: "Deadlock prevention: Banker's Algorithm is an example of?",
        opts: ["Avoidance", "Prevention", "Detection", "Recovery"],
        correct: 0,
        subj: "Operating Systems",
        marks: 2,
      },
      {
        id: 7,
        text: "Which layer in OSI encrypts data?",
        opts: ["Network", "Transport", "Presentation", "Session"],
        correct: 2,
        subj: "Networks",
        marks: 2,
      },
      {
        id: 8,
        text: "Regular expression a* denotes?",
        opts: ["One or more a", "Zero or more a", "Exactly one a", "No a"],
        correct: 1,
        subj: "TOC",
        marks: 2,
      },
      {
        id: 9,
        text: "Which gate is universal?",
        opts: ["AND", "OR", "NAND", "XOR"],
        correct: 2,
        subj: "Digital Logic",
        marks: 2,
      },
      {
        id: 10,
        text: "Which of these is NOT a property of a good hash function?",
        opts: [
          "Uniform distribution",
          "Deterministic",
          "Reversible",
          "Efficient",
        ],
        correct: 2,
        subj: "Data Structures",
        marks: 2,
      },
    ],
  },
  {
    id: 2,
    title: "Engineering Physics Quiz",
    subject: "Engineering Physics",
    duration: 60,
    total_marks: 30,
    questions: [
      {
        id: 1,
        text: "Speed of light in vacuum?",
        opts: ["3×10⁸ m/s", "3×10⁶ m/s", "3×10¹⁰ m/s", "3×10⁴ m/s"],
        correct: 0,
        subj: "Optics",
        marks: 2,
      },
      {
        id: 2,
        text: "Which phenomenon proves wave nature of electrons?",
        opts: [
          "Photoelectric Effect",
          "Electron Diffraction",
          "Compton Effect",
          "Pair Production",
        ],
        correct: 1,
        subj: "Quantum Mechanics",
        marks: 2,
      },
      {
        id: 3,
        text: "Planck's constant h =",
        opts: [
          "6.63×10⁻³⁴ J·s",
          "9.11×10⁻³¹ kg",
          "1.67×10⁻²⁷ kg",
          "1.6×10⁻¹⁹ C",
        ],
        correct: 0,
        subj: "Quantum Mechanics",
        marks: 2,
      },
      {
        id: 4,
        text: "Energy of a photon E =",
        opts: ["mc²", "hν", "½mv²", "qV"],
        correct: 1,
        subj: "Quantum Mechanics",
        marks: 2,
      },
      {
        id: 5,
        text: "Numerical aperture of an optical fibre depends on?",
        opts: [
          "Refractive indices of core and cladding",
          "Core diameter only",
          "Wavelength only",
          "Temperature only",
        ],
        correct: 0,
        subj: "Optics",
        marks: 2,
      },
    ],
  },
  {
    id: 3,
    title: "JEE Mathematics — Practice",
    subject: "JEE",
    duration: 90,
    total_marks: 40,
    questions: [
      {
        id: 1,
        text: "d/dx(x²) =",
        opts: ["x", "2x", "2x²", "x/2"],
        correct: 1,
        subj: "Calculus",
        marks: 4,
      },
      {
        id: 2,
        text: "∫cos(x)dx =",
        opts: ["sin(x)+C", "-sin(x)+C", "tan(x)+C", "-cos(x)+C"],
        correct: 0,
        subj: "Calculus",
        marks: 4,
      },
      {
        id: 3,
        text: "Roots of x²-5x+6=0 are:",
        opts: ["2,3", "1,6", "-2,-3", "2,-3"],
        correct: 0,
        subj: "Algebra",
        marks: 4,
      },
      {
        id: 4,
        text: "Number of diagonals in a hexagon:",
        opts: ["6", "9", "12", "15"],
        correct: 1,
        subj: "Algebra",
        marks: 4,
      },
    ],
  },
  {
    id: 4,
    title: "UPSC GS Paper I — Practice",
    subject: "UPSC",
    duration: 120,
    total_marks: 50,
    questions: [
      {
        id: 1,
        text: "Indian Constitution was adopted on:",
        opts: ["15 Aug 1947", "26 Jan 1950", "26 Nov 1949", "1 Jan 1950"],
        correct: 2,
        subj: "Polity",
        marks: 2,
      },
      {
        id: 2,
        text: "Ganga originates from:",
        opts: ["Gangotri", "Yamunotri", "Kedarnath", "Satopanth"],
        correct: 0,
        subj: "Geography",
        marks: 2,
      },
      {
        id: 3,
        text: "Non-Cooperation Movement started in:",
        opts: ["1919", "1920", "1921", "1922"],
        correct: 1,
        subj: "History",
        marks: 2,
      },
      {
        id: 4,
        text: "Which Article abolishes untouchability?",
        opts: ["Article 14", "Article 15", "Article 17", "Article 19"],
        correct: 2,
        subj: "Polity",
        marks: 2,
      },
    ],
  },
];

const BOT_KW = {
  greet: ["hello", "hi", "hey", "namaste"],
  gate: ["gate"],
  jee: ["jee", "iit"],
  neet: ["neet", "medical"],
  upsc: ["upsc", "ias"],
  weak: ["weak", "difficult", "struggling"],
  mock: ["mock", "test strategy"],
  pyq: ["pyq", "previous year"],
  motivation: ["demotivated", "tired", "give up", "motivation"],
  schedule: ["schedule", "timetable", "routine"],
  notes: ["notes", "note making", "revision"],
};
const BOT_RESP = {
  greet: [
    "Hi! 👋 I'm StudySaathi AI. Ask me anything about exam prep!",
    "Hello! Ready to help you crack your exam 🚀",
  ],
  gate: [
    "GATE CS: Engg Maths 13%, Algo+DS 15%, DBMS+OS+CN 20%. Last 10 years PYQs are mandatory. Never guess 2-mark questions!",
    "For GATE, focus on high-weightage: Algorithms, OS, DBMS, CN, Engg Maths. Practice PYQs topic-wise every day.",
  ],
  jee: [
    "JEE tip: NCERT Chemistry is the syllabus. Physics: concepts first, then numericals. Math: Calculus + Coordinate Geometry = highest weight.",
    "Class 11 = ~47% of JEE. Don't neglect Mechanics, Thermodynamics, and Organic Chemistry basics!",
  ],
  neet: [
    "NEET: Biology = 50% of marks. Master NCERT Biology line by line. Every diagram matters. Revise inorganic Chemistry from NCERT only.",
    "For NEET, Biology is king. 360/720 marks come from Biology alone. Spend at least 60% of your time there.",
  ],
  upsc: [
    "UPSC: NCERT books 6-12 are the foundation. Read The Hindu daily. Answer writing practice is non-negotiable for Mains.",
    "For UPSC Prelims: Polity (Laxmikant), History (Spectrum), Geography (NCERT), Economy (Ramesh Singh). All mandatory.",
  ],
  weak: [
    "Weak subject approach: break it to smallest topics → textbook + video → 3 PYQs per topic → spaced repetition every 3 days.",
    "Use active recall, not passive reading. After studying, close the book and write what you remember. That's real learning!",
  ],
  mock: [
    "Mock test strategy: Spend 2× more time reviewing wrong answers than giving tests. Analyse WHY each answer was wrong.",
    "After each mock: correct (why), wrong (concept gap), guessed. This 3-column analysis is more valuable than the test itself.",
  ],
  pyq: [
    "PYQ strategy: Start every new topic by reading its PYQs first. ~30% of GATE concepts repeat yearly!",
    "PYQs tell you exactly what to study. In UPSC, PYQs practically define the syllabus. Never skip them.",
  ],
  motivation: [
    "Remember why you started. Consistency today = rank tomorrow. Study for just 25 minutes — START NOW! 💪",
    "The gap between where you are and where you want to be is closed only by daily action. You've got this!",
  ],
  schedule: [
    "Effective schedule: 50-min focus + 10-min break. Hard subjects in the morning. Revise within 24 hours of learning.",
    "Try time-blocking: fixed slots to each subject. Consistency beats intensity every time.",
  ],
  notes: [
    "Smart notes: Cornell Method — questions left, notes right, summary at bottom. Revise within 24 hours of making them.",
    "After each chapter: close everything and write a 1-page memory dump. Gaps = topics to revise. #1 study hack.",
  ],
  default: [
    "Great question! Ask me about GATE, JEE, NEET, UPSC, study schedules, PYQ tips, or motivation. I'm here to help! 🚀",
    "I'm StudySaathi AI. Ask me anything about exam prep, study strategies, or subject doubts.",
  ],
};
function botReply(msg) {
  const m = msg.toLowerCase();
  for (const [k, kws] of Object.entries(BOT_KW)) {
    if (kws.some((kw) => m.includes(kw))) {
      const r = BOT_RESP[k];
      return r[Math.floor(Math.random() * r.length)];
    }
  }
  return BOT_RESP.default[Math.floor(Math.random() * BOT_RESP.default.length)];
}

const ACHIEVEMENTS = [
  {
    id: "streak7",
    icon: "🔥",
    name: "7-Day Streak",
    desc: "Study 7 days in a row",
    check: (u) => (u.streak || 0) >= 7,
  },
  {
    id: "streak30",
    icon: "⚡",
    name: "30-Day Streak",
    desc: "Study 30 days in a row",
    check: (u) => (u.streak || 0) >= 30,
  },
  {
    id: "subj_master",
    icon: "📚",
    name: "Subject Master",
    desc: "Complete a subject 100%",
    check: (u, subs) =>
      subs.some(
        (s) =>
          (s.topics || []).length > 0 &&
          (s.topics || []).every((t) => t.status === "completed"),
      ),
  },
  {
    id: "mock_champ",
    icon: "🏆",
    name: "Mock Champion",
    desc: "Score 80%+ in a test",
    check: (u, _, scores) => scores.some((s) => s.pct >= 80),
  },
  {
    id: "pyq_expert",
    icon: "📝",
    name: "PYQ Expert",
    desc: "Answer 50+ PYQs",
    check: (u) => (u.pyq_answered || 0) >= 50,
  },
  {
    id: "first_test",
    icon: "🧪",
    name: "First Test",
    desc: "Complete first mock test",
    check: (u, _, scores) => scores.length > 0,
  },
  {
    id: "planner",
    icon: "📅",
    name: "Master Planner",
    desc: "Generate a study plan",
    check: (u) => (u.plans_gen || 0) > 0,
  },
  {
    id: "consistent",
    icon: "💎",
    name: "Consistent Learner",
    desc: "Log hours for 10 days",
    check: (u) => (u.study_days || 0) >= 10,
  },
];

const MockAPI = {
  async req(method, path, body) {
    await new Promise((r) => setTimeout(r, 75));
    const u = DB.uid();
    if (path === "/auth/register" && method === "POST") {
      const users = DB.get("users", []);
      if (users.find((x) => x.email === body.email))
        throw new Error("Email already registered");
      const user = {
        id: Date.now(),
        name: body.name,
        email: body.email,
        password: body.password,
        course: body.course || "",
        semester: body.semester || 1,
        exam: body.exam || "",
        streak: 0,
        study_days: 0,
        pyq_answered: 0,
        plans_gen: 0,
      };
      users.push(user);
      DB.set("users", users);
      return {
        token: "ss3_" + Math.random().toString(36).slice(2),
        user: {
          id: user.id,
          name: user.name,
          email: user.email,
          course: user.course,
          semester: user.semester,
          exam: user.exam,
        },
      };
    }
    if (path === "/auth/login" && method === "POST") {
      const user = DB.get("users", []).find(
        (x) => x.email === body.email && x.password === body.password,
      );
      if (!user) throw new Error("Invalid email or password");
      return {
        token: "ss3_" + Math.random().toString(36).slice(2),
        user: {
          id: user.id,
          name: user.name,
          email: user.email,
          course: user.course,
          semester: user.semester,
          exam: user.exam,
        },
      };
    }
    if (path === "/auth/logout") return { message: "Logged out" };
    if (path === "/auth/me") {
      const au = Auth.user();
      if (!au) throw new Error("Unauthorized");
      return { user: au };
    }
    if (path === "/auth/profile" && method === "PATCH") {
      const users = DB.get("users", []);
      const usr = users.find((x) => x.id === u);
      if (!usr) throw new Error("Not found");
      Object.assign(usr, body);
      DB.set("users", users);
      const upd = { ...Auth.user(), ...usr };
      localStorage.setItem("ss3_user", JSON.stringify(upd));
      return { user: upd };
    }
    if (path === "/dashboard") {
      const today = todayStr(),
        prog = DB.get("prog_" + u, []),
        subs = DB.get("subs_" + u, []),
        tasks = DB.get("tasks_" + u, [])
          .filter((t) => t.date === today)
          .reverse()
          .slice(0, 8),
        exams = DB.get("exams_" + u, [])
          .filter((e) => e.exam_date >= today)
          .map((e) => ({ ...e, days_left: daysLeft(e.exam_date) }))
          .sort((a, b) => (a.exam_date > b.exam_date ? 1 : -1))
          .slice(0, 5);
      const todayH = prog
        .filter((p) => p.date === today)
        .reduce((s, p) => s + p.hours, 0);
      const allT = subs.flatMap((s) => s.topics || []),
        doneT = allT.filter((t) => t.status === "completed").length;
      const sd = [...new Set(prog.map((p) => p.date))].sort().reverse();
      let streak = 0;
      for (let i = 0; i < 60; i++) {
        const d = new Date(today);
        d.setDate(d.getDate() - i);
        if (sd.includes(d.toISOString().split("T")[0])) streak++;
        else if (i > 0) break;
      }
      const scores = DB.get("scores_" + u, []);
      const avgScore = scores.length
        ? Math.round(scores.reduce((s, x) => s + x.pct, 0) / scores.length)
        : 0;
      return {
        user: Auth.user(),
        date: today,
        tasks,
        exams,
        hours_today: Math.round(todayH * 10) / 10,
        tasks_total: tasks.length,
        tasks_done: tasks.filter((t) => t.status === "done").length,
        subject_count: subs.length,
        syllabus_pct: allT.length ? Math.round((doneT / allT.length) * 100) : 0,
        streak,
        avg_mock: avgScore,
        total_tests: scores.length,
        recommendations: _recs(u, subs, prog, scores, exams),
      };
    }
    if (path === "/subjects" && method === "GET")
      return { subjects: DB.get("subs_" + u, []) };
    if (path === "/subjects" && method === "POST") {
      const subs = DB.get("subs_" + u, []);
      const sub = {
        id: Date.now(),
        name: body.name,
        topics: [],
        created_at: new Date().toISOString(),
      };
      subs.push(sub);
      DB.set("subs_" + u, subs);
      return { message: "Added", ...sub };
    }
    if (/^\/subjects\/\d+$/.test(path) && method === "DELETE") {
      DB.set(
        "subs_" + u,
        DB.get("subs_" + u, []).filter(
          (s) => s.id !== parseInt(path.split("/")[2]),
        ),
      );
      return { message: "Deleted" };
    }
    if (/^\/subjects\/\d+\/topics$/.test(path) && method === "POST") {
      const sid = parseInt(path.split("/")[2]),
        subs = DB.get("subs_" + u, []),
        sub = subs.find((s) => s.id === sid);
      if (!sub) throw new Error("Not found");
      const t = {
        id: Date.now(),
        name: body.name,
        priority: body.priority || getTopicPriority(body.name),
        status: "not_started",
        notes: "",
      };
      (sub.topics = sub.topics || []).push(t);
      DB.set("subs_" + u, subs);
      return { ...t };
    }
    if (/^\/subjects\/topics\/\d+$/.test(path) && method === "PATCH") {
      const tid = parseInt(path.split("/")[3]),
        subs = DB.get("subs_" + u, []);
      for (const s of subs) {
        const t = (s.topics || []).find((x) => x.id === tid);
        if (t) {
          Object.assign(t, body);
          break;
        }
      }
      DB.set("subs_" + u, subs);
      return { message: "Updated" };
    }
    if (/^\/subjects\/topics\/\d+$/.test(path) && method === "DELETE") {
      const tid = parseInt(path.split("/")[3]),
        subs = DB.get("subs_" + u, []);
      for (const s of subs)
        s.topics = (s.topics || []).filter((x) => x.id !== tid);
      DB.set("subs_" + u, subs);
      return { message: "Deleted" };
    }
    if (path.startsWith("/tasks") && method === "GET") {
      const qs = path.includes("?") ? path.split("?")[1] : "";
      const date = new URLSearchParams(qs).get("date") || todayStr();
      return {
        tasks: DB.get("tasks_" + u, [])
          .filter((t) => t.date === date)
          .reverse(),
        date,
      };
    }
    if (path === "/tasks" && method === "POST") {
      const tasks = DB.get("tasks_" + u, []);
      const t = {
        id: Date.now(),
        task: body.task,
        priority: body.priority || "Medium",
        status: "pending",
        date: body.date || todayStr(),
      };
      tasks.push(t);
      DB.set("tasks_" + u, tasks);
      return { ...t };
    }
    if (/^\/tasks\/\d+$/.test(path) && method === "PATCH") {
      const tid = parseInt(path.split("/")[2]);
      const tasks = DB.get("tasks_" + u, []);
      const t = tasks.find((x) => x.id === tid);
      if (t) Object.assign(t, body);
      DB.set("tasks_" + u, tasks);
      return { message: "Updated" };
    }
    if (/^\/tasks\/\d+$/.test(path) && method === "DELETE") {
      DB.set(
        "tasks_" + u,
        DB.get("tasks_" + u, []).filter(
          (t) => t.id !== parseInt(path.split("/")[2]),
        ),
      );
      return { message: "Deleted" };
    }
    if (path === "/exams" && method === "GET")
      return {
        exams: DB.get("exams_" + u, [])
          .map((e) => ({ ...e, days_left: daysLeft(e.exam_date) }))
          .sort((a, b) => (a.exam_date > b.exam_date ? 1 : -1)),
      };
    if (path === "/exams" && method === "POST") {
      const exams = DB.get("exams_" + u, []);
      const e = { id: Date.now(), ...body };
      exams.push(e);
      DB.set("exams_" + u, exams);
      return { ...e };
    }
    if (/^\/exams\/\d+$/.test(path) && method === "DELETE") {
      DB.set(
        "exams_" + u,
        DB.get("exams_" + u, []).filter(
          (e) => e.id !== parseInt(path.split("/")[2]),
        ),
      );
      return { message: "Deleted" };
    }
    if (path === "/progress" && method === "GET") {
      const today = todayStr(),
        prog = DB.get("prog_" + u, []),
        subs = DB.get("subs_" + u, []);
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
              prog
                .filter((p) => p.date === ds)
                .reduce((s, p) => s + p.hours, 0) * 10,
            ) / 10,
        });
      }
      const smap = {};
      for (const p of prog) {
        if (!smap[p.subject])
          smap[p.subject] = { subject: p.subject, total: 0, days: new Set() };
        smap[p.subject].total += p.hours;
        smap[p.subject].days.add(p.date);
      }
      const by_subject = Object.values(smap)
        .map((s) => ({
          ...s,
          total: Math.round(s.total * 10) / 10,
          days: s.days.size,
        }))
        .sort((a, b) => b.total - a.total);
      const tc = subs.map((s, i) => {
        const tot = (s.topics || []).length,
          done = (s.topics || []).filter(
            (t) => t.status === "completed",
          ).length;
        return {
          subject: s.name,
          total: tot,
          done,
          pct: tot ? Math.round((done / tot) * 100) : 0,
          color: PALETTE[i % PALETTE.length],
        };
      });
      const sd = [...new Set(prog.map((p) => p.date))].sort().reverse();
      let streak = 0;
      for (let i = 0; i < 60; i++) {
        const d = new Date(today);
        d.setDate(d.getDate() - i);
        if (sd.includes(d.toISOString().split("T")[0])) streak++;
        else if (i > 0) break;
      }
      const todayH = prog
        .filter((p) => p.date === today)
        .reduce((s, p) => s + p.hours, 0);
      return {
        weekly,
        by_subject,
        topic_completion: tc,
        hours_today: Math.round(todayH * 10) / 10,
        streak,
        study_dates: sd,
        total_hours:
          Math.round(prog.reduce((s, p) => s + p.hours, 0) * 10) / 10,
      };
    }
    if (path === "/progress" && method === "POST") {
      const progs = DB.get("prog_" + u, []);
      const p = {
        id: Date.now(),
        subject: body.subject,
        hours: body.hours,
        notes: body.notes || "",
        date: body.date || todayStr(),
      };
      progs.push(p);
      DB.set("prog_" + u, progs);
      const users = DB.get("users", []);
      const usr = users.find((x) => x.id === u);
      if (usr) {
        usr.study_days = (usr.study_days || 0) + 1;
        DB.set("users", users);
      }
      return { ...p };
    }
    if (path === "/analytics" && method === "GET") {
      const prog = DB.get("prog_" + u, []),
        subs = DB.get("subs_" + u, []),
        scores = DB.get("scores_" + u, []);
      const monthly = [];
      for (let i = 29; i >= 0; i--) {
        const d = new Date();
        d.setDate(d.getDate() - i);
        const ds = d.toISOString().split("T")[0];
        monthly.push({
          date: ds,
          hours:
            Math.round(
              prog
                .filter((p) => p.date === ds)
                .reduce((s, p) => s + p.hours, 0) * 10,
            ) / 10,
        });
      }
      const allT = subs.flatMap((s) => s.topics || []),
        doneT = allT.filter((t) => t.status === "completed").length;
      const avg = scores.length
        ? Math.round(scores.reduce((s, x) => s + x.pct, 0) / scores.length)
        : 0;
      const best = scores.length ? Math.max(...scores.map((s) => s.pct)) : 0;
      return {
        monthly,
        scores,
        total_hours:
          Math.round(prog.reduce((s, p) => s + p.hours, 0) * 10) / 10,
        syllabus_pct: allT.length ? Math.round((doneT / allT.length) * 100) : 0,
        total_tests: scores.length,
        avg_score: avg,
        best_score: best,
      };
    }
    if (path.startsWith("/pyqs") && method === "GET") {
      const qs = path.includes("?") ? path.split("?")[1] : "",
        p = new URLSearchParams(qs);
      let data = [...PYQ_SEED, ...DB.get("pyqs_u_" + u, [])];
      if (p.get("subject"))
        data = data.filter((q) => q.subject === p.get("subject"));
      if (p.get("exam")) data = data.filter((q) => q.exam === p.get("exam"));
      if (p.get("year"))
        data = data.filter((q) => q.year === parseInt(p.get("year")));
      if (p.get("diff"))
        data = data.filter((q) => q.difficulty === p.get("diff"));
      if (p.get("q")) {
        const s = p.get("q").toLowerCase();
        data = data.filter(
          (q) =>
            q.question.toLowerCase().includes(s) ||
            q.subject.toLowerCase().includes(s),
        );
      }
      return { pyqs: data, total: data.length };
    }
    if (path === "/pyqs" && method === "POST") {
      const pyqs = DB.get("pyqs_u_" + u, []);
      const pq = {
        id: Date.now() + Math.random(),
        ...body,
        frequency: 1,
        importance: 70,
      };
      pyqs.push(pq);
      DB.set("pyqs_u_" + u, pyqs);
      return { ...pq };
    }
    if (path === "/mocktests" && method === "GET") return { tests: TEST_SEED };
    if (/^\/mocktests\/\d+$/.test(path) && method === "GET") {
      const id = parseInt(path.split("/")[2]);
      const t = TEST_SEED.find((x) => x.id === id);
      if (!t) throw new Error("Not found");
      return { test: t };
    }
    if (path === "/mocktests/submit" && method === "POST") {
      const { test_id, answers, time_taken } = body;
      const test = TEST_SEED.find((x) => x.id === test_id);
      if (!test) throw new Error("Not found");
      let correct = 0,
        wrong = 0,
        skipped = 0,
        obtained = 0;
      const tmap = {};
      const detailed = test.questions.map((q) => {
        const ans = answers[q.id],
          skip = ans === undefined || ans === null;
        const ok = !skip && parseInt(ans) === q.correct;
        if (skip) skipped++;
        else if (ok) {
          correct++;
          obtained += q.marks;
        } else wrong++;
        const s = q.subj;
        if (!tmap[s]) tmap[s] = { subject: s, correct: 0, wrong: 0, total: 0 };
        tmap[s].total++;
        if (ok) tmap[s].correct++;
        else if (!skip) tmap[s].wrong++;
        return {
          ...q,
          user_answer: ans === undefined ? null : parseInt(ans),
          is_correct: ok,
          skipped: skip,
        };
      });
      const tm = test.questions.reduce((s, q) => s + q.marks, 0);
      const pct = Math.round((obtained / tm) * 100);
      const grade = pct >= 80 ? "A" : pct >= 65 ? "B" : pct >= 50 ? "C" : "D";
      const score = {
        id: Date.now(),
        test_id,
        test_title: test.title,
        correct,
        wrong,
        skipped,
        total: test.questions.length,
        obtained,
        total_marks: tm,
        pct,
        time_taken,
        grade,
        date: todayStr(),
      };
      const scores = DB.get("scores_" + u, []);
      scores.unshift(score);
      DB.set("scores_" + u, scores.slice(0, 50));
      const weak = Object.values(tmap).filter(
        (t) => t.total > 0 && t.correct / t.total < 0.5,
      );
      return { score, detailed, weak_topics: weak, grade };
    }
    if (path === "/scores" && method === "GET")
      return { scores: DB.get("scores_" + u, []) };
    if (path === "/planner/generate" && method === "POST") {
      const { exam_date, daily_hours, mode, subjects } = body;
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const exam = new Date(exam_date + "T00:00:00");
      const dl = Math.max(1, Math.ceil((exam - today) / 86400000));
      const rev = Math.max(1, Math.floor(dl * 0.2));
      const sd = dl - rev;
      const tips = [];
      if (dl <= 7)
        tips.push("🚨 Critical: Focus ONLY on revision and past papers.");
      if (mode === "crash")
        tips.push("⚡ Crash mode: High-priority topics and PYQs only.");
      if (mode === "topper")
        tips.push("🏆 Topper mode: Deep coverage + daily mock tests.");
      const high = subjects.filter((s) => s.priority === "High");
      if (high.length)
        tips.push(
          `📖 High-priority: ${high.map((s) => s.name).join(", ")} — schedule mornings.`,
        );
      tips.push("💧 5-min break every 50 minutes. Sleep 7-8 hours.");
      const hrsMap = {
        balanced: daily_hours,
        topper: Math.min(daily_hours + 2, 12),
        crash: Math.min(daily_hours + 4, 12),
        weekend: daily_hours,
        working: Math.max(daily_hours - 1, 2),
      };
      const hrs = hrsMap[mode] || daily_hours;
      const DN = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
      const days = [];
      for (let i = 0; i < Math.min(dl, 60); i++) {
        const d = new Date(today);
        d.setDate(d.getDate() + i);
        const ds = d.toISOString().split("T")[0];
        const isRev = i >= sd;
        const label = `${DN[d.getDay() === 0 ? 6 : d.getDay() - 1]}, ${ds}${isRev ? " — Revision" : ""}`;
        const slots = [];
        if (isRev) {
          slots.push(
            {
              start: "09:00",
              end: "10:30",
              subject: "Revision Session",
              type: "revision",
              tip: "Review all subjects",
            },
            { start: "10:30", end: "10:45", subject: "Break", type: "break" },
            {
              start: "10:45",
              end: "12:30",
              subject: "Past Papers",
              type: "revision",
              tip: "PYQ focus",
            },
            {
              start: "14:00",
              end: "16:00",
              subject: "Mock Test",
              type: "revision",
              tip: "Full timed test",
            },
          );
        } else {
          let t = 8 + (mode === "working" ? 2 : 0);
          for (let j = 0; j < hrs; j++) {
            const subj = subjects[(i * hrs + j) % Math.max(1, subjects.length)];
            slots.push({
              start: `${String(t).padStart(2, "0")}:00`,
              end: `${String(t + 1).padStart(2, "0")}:00`,
              subject: subj?.name || "Study",
              priority: subj?.priority || "Medium",
              type: "study",
              tip:
                subj?.priority === "High"
                  ? "Deep focus — no distractions"
                  : null,
            });
            t++;
            if (j === 1 && hrs > 3)
              slots.push({
                start: `${String(t).padStart(2, "0")}:00`,
                end: `${String(t).padStart(2, "0")}:15`,
                subject: "Break",
                type: "break",
              });
          }
          slots.push({
            start: `${String(t).padStart(2, "0")}:00`,
            end: `${String(t + 1).padStart(2, "0")}:00`,
            subject: "Daily Review",
            type: "revision",
            tip: "Review today's notes",
          });
        }
        days.push({ date: ds, day: i + 1, is_revision: isRev, label, slots });
      }
      const plan = {
        id: Date.now(),
        exam_date,
        mode,
        daily_hours: hrs,
        days_left: dl,
        study_days: sd,
        revision_days: rev,
        tips,
        days,
        created_at: new Date().toISOString(),
      };
      const plans = DB.get("plans_" + u, []);
      plans.unshift(plan);
      DB.set("plans_" + u, plans.slice(0, 10));
      const users = DB.get("users", []);
      const usr = users.find((x) => x.id === u);
      if (usr) {
        usr.plans_gen = (usr.plans_gen || 0) + 1;
        DB.set("users", users);
      }
      return { plan };
    }
    if (path === "/planner/saved" && method === "GET")
      return { plans: DB.get("plans_" + u, []) };
    if (/^\/planner\/\d+$/.test(path) && method === "GET") {
      const pid = parseInt(path.split("/")[2]);
      const plan = DB.get("plans_" + u, []).find((p) => p.id === pid);
      if (!plan) throw new Error("Not found");
      return { plan };
    }
    if (path.startsWith("/search") && method === "GET") {
      const qs = path.includes("?") ? path.split("?")[1] : "",
        q = (new URLSearchParams(qs).get("q") || "").toLowerCase();
      if (!q) return { results: [] };
      const subs = DB.get("subs_" + u, []);
      const results = [
        ...subs
          .filter((s) => s.name.toLowerCase().includes(q))
          .map((s) => ({
            type: "subject",
            title: s.name,
            sub: "Subject",
            href: "subjects.html",
          })),
        ...subs.flatMap((s) =>
          (s.topics || [])
            .filter((t) => t.name.toLowerCase().includes(q))
            .map((t) => ({
              type: "topic",
              title: t.name,
              sub: s.name,
              href: "subjects.html",
            })),
        ),
        ...[...PYQ_SEED, ...DB.get("pyqs_u_" + u, [])]
          .filter(
            (p) =>
              p.question.toLowerCase().includes(q) ||
              p.subject.toLowerCase().includes(q),
          )
          .map((p) => ({
            type: "pyq",
            title: p.question.slice(0, 65) + "…",
            sub: p.subject + " · " + p.year,
            href: "pyq.html",
          }))
          .slice(0, 5),
        ...TEST_SEED.filter(
          (t) =>
            t.title.toLowerCase().includes(q) ||
            t.subject.toLowerCase().includes(q),
        ).map((t) => ({
          type: "test",
          title: t.title,
          sub: t.subject,
          href: "mocktest.html",
        })),
      ];
      return { results: results.slice(0, 12) };
    }
    if (path === "/chat" && method === "POST")
      return { reply: botReply(body.message || "") };
    if (path === "/achievements" && method === "GET") {
      const users = DB.get("users", []);
      const usr = users.find((x) => x.id === u) || {};
      const scores = DB.get("scores_" + u, []);
      const subs = DB.get("subs_" + u, []);
      return {
        achievements: ACHIEVEMENTS.map((a) => ({
          ...a,
          unlocked: a.check(usr, subs, scores),
        })),
      };
    }
    if (path === "/notifications" && method === "GET") {
      const exams = DB.get("exams_" + u, [])
        .filter((e) => e.exam_date >= todayStr())
        .map((e) => ({ ...e, dl: daysLeft(e.exam_date) }));
      const notifs = [];
      exams
        .filter((e) => e.dl <= 7)
        .forEach((e) =>
          notifs.push({
            id: e.id,
            type: "exam",
            icon: "📅",
            title: `${e.subject} in ${e.dl} day(s)!`,
            time: "Now",
          }),
        );
      const prog = DB.get("prog_" + u, []);
      const todayH = prog
        .filter((p) => p.date === todayStr())
        .reduce((s, p) => s + p.hours, 0);
      if (todayH === 0)
        notifs.push({
          id: "log",
          type: "reminder",
          icon: "⏱",
          title: "Log today's study hours",
          time: "Today",
        });
      return { notifications: notifs, count: notifs.length };
    }
    throw new Error("MockAPI: unknown " + method + " " + path);
  },
};

function _recs(uid, subs, prog, scores, exams) {
  const r = [];
  subs.forEach((s) => {
    const tot = (s.topics || []).length,
      done = (s.topics || []).filter((t) => t.status === "completed").length;
    if (tot > 0 && done / tot < 0.4)
      r.push({
        type: "weak",
        icon: "📉",
        title: `Focus on ${s.name}`,
        msg: `Only ${Math.round((done / tot) * 100)}% complete.`,
      });
  });
  const hard = subs.flatMap((s) =>
    (s.topics || [])
      .filter((t) => t.priority === "High" && t.status === "not_started")
      .map((t) => ({ ...t, subject: s.name })),
  );
  if (hard.length)
    r.push({
      type: "hard",
      icon: "🔴",
      title: `${hard.length} high-priority topic(s) not started`,
      msg: `"${hard[0].name}" (${hard[0].subject}) needs attention.`,
    });
  exams
    .filter((e) => e.days_left >= 0 && e.days_left <= 14)
    .forEach((e) =>
      r.push({
        type: "exam",
        icon: "⚠️",
        title: `${e.subject} in ${Math.round(e.days_left)} days!`,
        msg: "Switch to intensive revision.",
      }),
    );
  if (scores.length > 0 && scores[0].pct < 50)
    r.push({
      type: "hard",
      icon: "📊",
      title: `Last mock: ${scores[0].pct}%`,
      msg: "Review wrong answers and revise weak topics.",
    });
  if (!r.length) {
    const wh = prog
      .filter((p) => (new Date() - new Date(p.date)) / 86400000 <= 7)
      .reduce((s, p) => s + p.hours, 0);
    r.push({
      type: "good",
      icon: "🌟",
      title:
        wh > 0
          ? `${wh.toFixed(1)}h this week — great job!`
          : "Welcome to StudySaathi!",
      msg:
        wh > 0
          ? "Keep the streak going!"
          : "Start adding subjects and logging study hours.",
    });
  }
  return r.slice(0, 5);
}

const _Real = {
  async r(m, p, b = null) {
    const h = { "Content-Type": "application/json" };
    const t = Auth.token();
    if (t) h.Authorization = `Bearer ${t}`;
    const o = { method: m, headers: h };
    if (b) o.body = JSON.stringify(b);
    const res = await fetch(API_BASE + p, o);
    const d = await res.json().catch(() => ({}));
    if (!res.ok) {
      if (res.status === 401 && !p.includes("/auth/")) {
        Auth.clear();
        location.href = "index.html";
        return;
      }
      throw new Error(d.error || `HTTP ${res.status}`);
    }
    return d;
  },
  get(p) {
    return this.r("GET", p);
  },
  post(p, b) {
    return this.r("POST", p, b);
  },
  patch(p, b) {
    return this.r("PATCH", p, b);
  },
  del(p) {
    return this.r("DELETE", p);
  },
};
const API = {
  get(p) {
    return USE_MOCK ? MockAPI.req("GET", p, null) : _Real.get(p);
  },
  post(p, b) {
    return USE_MOCK ? MockAPI.req("POST", p, b) : _Real.post(p, b);
  },
  patch(p, b) {
    return USE_MOCK ? MockAPI.req("PATCH", p, b) : _Real.patch(p, b);
  },
  del(p) {
    return USE_MOCK ? MockAPI.req("DELETE", p, null) : _Real.del(p);
  },
};

// UI helpers
function showToast(msg, type = "success", dur = 3500) {
  let c = document.getElementById("toast-container");
  if (!c) {
    c = document.createElement("div");
    c.id = "toast-container";
    document.body.appendChild(c);
  }
  const t = document.createElement("div");
  t.className = `toast ${type}`;
  const icons = { success: "✓", error: "✕", info: "ℹ", warn: "⚠" };
  t.innerHTML = `<span class="ti">${icons[type] || "✓"}</span> ${msg}`;
  c.appendChild(t);
  requestAnimationFrame(() => t.classList.add("show"));
  setTimeout(() => {
    t.classList.remove("show");
    setTimeout(() => t.remove(), 400);
  }, dur);
}
function setLoading(btn, on) {
  if (!btn) return;
  if (on) {
    btn._t = btn.innerHTML;
    btn.innerHTML = `<span class="spinner"></span> Please wait…`;
    btn.disabled = true;
  } else {
    btn.innerHTML = btn._t || btn.innerHTML;
    btn.disabled = false;
  }
}
function requireAuth() {
  if (!Auth.isAuth()) {
    location.href = "index.html";
    return false;
  }
  return true;
}
function redirectIfAuth() {
  if (Auth.isAuth()) location.href = "dashboard.html";
}
function openModal(id) {
  document.getElementById(id)?.classList.add("open");
}
function closeModal(id) {
  document.getElementById(id)?.classList.remove("open");
}
document.addEventListener("click", (e) => {
  if (e.target.classList.contains("modal-ov"))
    e.target.classList.remove("open");
});
function emptyHTML(icon, msg) {
  return `<div class="empty"><div class="empty-icon">${icon}</div><p>${msg}</p></div>`;
}
function loadHTML() {
  return `<div class="loading"><span class="spinner"></span> Loading…</div>`;
}
function progBarHTML(name, pct, color) {
  return `<div class="prog-wrap"><div class="prog-head"><span>${name}</span><span class="prog-pct">${pct}%</span></div><div class="prog-bar"><div class="prog-fill" style="width:${pct}%;background:${color || "var(--indigo)"}"></div></div></div>`;
}
function buildBarChart(id, data, maxVal) {
  const w = document.getElementById(id);
  if (!w) return;
  const max = maxVal || Math.max(...data.map((d) => d.v), 0.1);
  w.innerHTML = data
    .map(
      (d, i) =>
        `<div class="bc-col"><div class="bc-val">${d.v}h</div><div class="bc-bar animated" style="height:${Math.max(3, Math.round((d.v / max) * 120))}px;background:${d.c || "var(--indigo)"};animation-delay:${i * 0.06}s"></div><div class="bc-lbl">${d.l}</div></div>`,
    )
    .join("");
}
function populateNav() {
  const u = Auth.user();
  if (!u) return;
  const e = document.getElementById("nav-user-name");
  if (e) e.textContent = u.name?.split(" ")[0] || "User";
  const a = document.getElementById("nav-avatar");
  if (a) a.textContent = (u.name || "U")[0].toUpperCase();
  const a2 = document.getElementById("nav-avatar2");
  if (a2) a2.textContent = (u.name || "U")[0].toUpperCase();
}
async function logout() {
  try {
    await API.post("/auth/logout");
  } catch (_) {}
  Auth.clear();
  location.href = "index.html";
}
function badgeHTML(v, map) {
  return `<span class="badge ${map[v] || "b-muted"}">${v}</span>`;
}
const PMAP = { High: "b-red", Medium: "b-gold", Low: "b-green" };
const DMAP = { Hard: "b-red", Medium: "b-gold", Easy: "b-green" };
function setupHamburger() {
  const h = document.getElementById("hamburger");
  const s = document.querySelector(".sidebar");
  if (!h || !s) return;
  h.addEventListener("click", () => s.classList.toggle("open"));
  document.addEventListener("click", (e) => {
    if (!s.contains(e.target) && !h.contains(e.target))
      s.classList.remove("open");
  });
}
function setupTheme() {
  const saved = localStorage.getItem("ss3_theme") || "dark";
  document.documentElement.setAttribute("data-theme", saved);
  const t = document.getElementById("theme-toggle");
  if (t)
    t.addEventListener("click", () => {
      const cur = document.documentElement.getAttribute("data-theme");
      const next = cur === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      localStorage.setItem("ss3_theme", next);
    });
}
function setupSearch() {
  const inp = document.getElementById("search-inp");
  if (!inp) return;
  let tmr;
  inp.addEventListener("input", () => {
    clearTimeout(tmr);
    const q = inp.value.trim();
    if (q.length < 2) {
      document.getElementById("search-results")?.classList.remove("open");
      return;
    }
    tmr = setTimeout(async () => {
      try {
        const d = await API.get("/search?q=" + encodeURIComponent(q));
        const icons = { subject: "📚", topic: "📖", pyq: "📝", test: "🧪" };
        let dr = document.getElementById("search-results");
        if (!dr) {
          dr = document.createElement("div");
          dr.id = "search-results";
          document.querySelector(".topbar-search")?.appendChild(dr);
        }
        dr.innerHTML = d.results.length
          ? d.results
              .map(
                (x) =>
                  `<div class="sr-item" onclick="location.href='${x.href}'"><span class="sr-type">${icons[x.type] || "🔍"}</span><div><div class="sr-title">${x.title}</div>${x.sub ? `<div class="sr-sub">${x.sub}</div>` : ""}</div></div>`,
              )
              .join("")
          : emptyHTML("🔍", "No results");
        dr.classList.add("open");
      } catch (_) {}
    }, 280);
  });
  inp.addEventListener("blur", () =>
    setTimeout(
      () => document.getElementById("search-results")?.classList.remove("open"),
      200,
    ),
  );
}
function setupNotifications() {
  const btn = document.getElementById("notif-btn");
  if (!btn) return;
  const panel = document.getElementById("notif-panel");
  btn.addEventListener("click", async (e) => {
    e.stopPropagation();
    try {
      const d = await API.get("/notifications");
      const dot = document.querySelector(".tb-dot");
      if (dot) dot.style.display = d.count ? "" : "none";
      if (panel) {
        panel.innerHTML =
          `<div class="notif-hdr"><span class="notif-ttl">Notifications</span><span style="font-size:.78rem;color:var(--text2)">${d.count} new</span></div>` +
          (d.notifications.length
            ? d.notifications
                .map(
                  (n) =>
                    `<div class="notif-item"><div class="notif-icon" style="background:rgba(61,90,241,.1)">${n.icon}</div><div><div class="notif-title">${n.title}</div><div class="notif-time">${n.time}</div></div></div>`,
                )
                .join("")
            : emptyHTML("🔔", "No notifications"));
      }
    } catch (_) {}
    panel?.classList.toggle("open");
  });
  document.addEventListener("click", (e) => {
    if (panel && !panel.contains(e.target) && !btn.contains(e.target))
      panel.classList.remove("open");
  });
}
function setupChatFab() {
  const fab = document.querySelector(".chat-fab");
  const panel = document.querySelector(".chat-panel");
  if (!fab || !panel) return;
  fab.addEventListener("click", () => panel.classList.toggle("open"));
  document
    .querySelector(".chat-close")
    ?.addEventListener("click", () => panel.classList.remove("open"));
}
async function handleChatSend() {
  const inp = document.getElementById("chat-fab-inp");
  if (!inp || !inp.value.trim()) return;
  const msg = inp.value.trim();
  inp.value = "";
  _appendMsg(msg, "user");
  _showTyping();
  try {
    const d = await API.post("/chat", { message: msg });
    _removeTyping();
    _appendMsg(d.reply, "bot");
  } catch (_) {
    _removeTyping();
    _appendMsg("Sorry, I ran into an issue. Try again! 😅", "bot");
  }
}
function _appendMsg(text, role) {
  const area = document.getElementById("chat-fab-msgs");
  if (!area) return;
  const div = document.createElement("div");
  div.className = "msg " + role;
  const ini =
    role === "user" ? (Auth.user()?.name || "U")[0].toUpperCase() : "🤖";
  div.innerHTML = `<div class="msg-av">${ini}</div><div class="msg-bub">${text.replace(/\n/g, "<br>")}</div>`;
  area.appendChild(div);
  area.scrollTop = area.scrollHeight;
}
function _showTyping() {
  const area = document.getElementById("chat-fab-msgs");
  if (!area) return;
  const d = document.createElement("div");
  d.className = "msg bot";
  d.id = "typing-ind";
  d.innerHTML = `<div class="msg-av">🤖</div><div class="msg-bub" style="display:flex;gap:5px;align-items:center;padding:12px 16px"><div class="td-dot"></div><div class="td-dot"></div><div class="td-dot"></div></div>`;
  area.appendChild(d);
  area.scrollTop = area.scrollHeight;
}
function _removeTyping() {
  document.getElementById("typing-ind")?.remove();
}
function setupScrollReveal() {
  const obs = new IntersectionObserver(
    (entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) e.target.classList.add("visible");
      });
    },
    { threshold: 0.12 },
  );
  document.querySelectorAll(".reveal").forEach((el) => obs.observe(el));
}
function setupDropdowns() {
  document.querySelectorAll(".dd-toggle").forEach((btn) =>
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      btn
        .closest(".dropdown")
        .querySelector(".dd-menu")
        ?.classList.toggle("open");
    }),
  );
  document.addEventListener("click", () => {
    document
      .querySelectorAll(".dd-menu.open")
      .forEach((m) => m.classList.remove("open"));
  });
}
document.addEventListener("DOMContentLoaded", () => {
  populateNav();
  setupHamburger();
  setupTheme();
  setupSearch();
  setupNotifications();
  setupChatFab();
  setupScrollReveal();
  setupDropdowns();
  document.getElementById("chat-fab-inp")?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") handleChatSend();
  });
  document
    .querySelector(".chat-send")
    ?.addEventListener("click", handleChatSend);
});
