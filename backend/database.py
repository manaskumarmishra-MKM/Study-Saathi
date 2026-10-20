"""database.py — StudySaathi v3 © Manas Kumar Mishra"""
import sqlite3, os
DB_PATH = os.path.join(os.path.dirname(__file__), "../database/studysaathi.db")
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,email TEXT UNIQUE NOT NULL,password TEXT NOT NULL,course TEXT DEFAULT '',semester INTEGER DEFAULT 1,exam TEXT DEFAULT '',daily_goal INTEGER DEFAULT 6,streak INTEGER DEFAULT 0,study_days INTEGER DEFAULT 0,pyq_answered INTEGER DEFAULT 0,plans_gen INTEGER DEFAULT 0,created_at TEXT DEFAULT(datetime('now')));
    CREATE TABLE IF NOT EXISTS subjects(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,name TEXT NOT NULL,created_at TEXT DEFAULT(datetime('now')));
    CREATE TABLE IF NOT EXISTS topics(id INTEGER PRIMARY KEY AUTOINCREMENT,subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,name TEXT NOT NULL,priority TEXT DEFAULT 'Medium',status TEXT DEFAULT 'not_started',notes TEXT DEFAULT '',created_at TEXT DEFAULT(datetime('now')));
    CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,task TEXT NOT NULL,priority TEXT DEFAULT 'Medium',status TEXT DEFAULT 'pending',date TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS exams(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,subject TEXT NOT NULL,exam_date TEXT NOT NULL,notes TEXT DEFAULT '');
    CREATE TABLE IF NOT EXISTS progress(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,subject TEXT NOT NULL,hours REAL NOT NULL,notes TEXT DEFAULT '',date TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS pyqs(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,subject TEXT NOT NULL,exam TEXT NOT NULL,year INTEGER NOT NULL,unit TEXT DEFAULT '',question TEXT NOT NULL,answer TEXT NOT NULL,difficulty TEXT DEFAULT 'Medium',frequency INTEGER DEFAULT 1,importance INTEGER DEFAULT 70,is_verified INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS scores(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,test_id INTEGER NOT NULL,test_title TEXT NOT NULL,correct INTEGER,wrong INTEGER,skipped INTEGER,total INTEGER,obtained INTEGER,total_marks INTEGER,pct INTEGER,time_taken INTEGER,grade TEXT,date TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS study_plans(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,exam_date TEXT NOT NULL,mode TEXT DEFAULT 'balanced',daily_hours INTEGER,plan_json TEXT NOT NULL,created_at TEXT DEFAULT(datetime('now')));
    """)
    db.commit(); db.close()
    print("✅ Database initialised:", DB_PATH)
