"""
app.py — StudySaathi v3 Flask Backend
© Manas Kumar Mishra. All rights reserved.
Run: python app.py
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from database import init_db, get_db
from models import auth_required, hash_pw, check_pw, make_token
from datetime import date, timedelta
import json, random

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ── Auth ──────────────────────────────────────────────────────
@app.route("/api/auth/register", methods=["POST"])
def register():
    d=request.get_json() or {}
    name=d.get("name","").strip(); email=d.get("email","").strip().lower(); pw=d.get("password","")
    if not name or not email or not pw: return jsonify({"error":"Name, email and password required"}),400
    if len(pw)<6: return jsonify({"error":"Password must be at least 6 characters"}),400
    db=get_db()
    if db.execute("SELECT id FROM users WHERE email=?",[email]).fetchone():
        return jsonify({"error":"Email already registered"}),409
    db.execute("INSERT INTO users(name,email,password,course,semester,exam) VALUES(?,?,?,?,?,?)",
               [name,email,hash_pw(pw),d.get("course",""),d.get("semester",1),d.get("exam","")])
    db.commit()
    user=db.execute("SELECT * FROM users WHERE email=?",[email]).fetchone()
    return jsonify({"token":make_token(user["id"],user["name"],user["email"]),
                    "user":_ud(user)}),201

@app.route("/api/auth/login", methods=["POST"])
def login():
    d=request.get_json() or {}
    db=get_db()
    user=db.execute("SELECT * FROM users WHERE email=?",[d.get("email","").lower()]).fetchone()
    if not user or not check_pw(d.get("password",""),user["password"]):
        return jsonify({"error":"Invalid email or password"}),401
    return jsonify({"token":make_token(user["id"],user["name"],user["email"]),"user":_ud(user)})

@app.route("/api/auth/logout", methods=["POST"])
def logout(): return jsonify({"message":"Logged out"})

@app.route("/api/auth/me")
@auth_required
def me(u):
    db=get_db(); user=db.execute("SELECT * FROM users WHERE id=?",[u["id"]]).fetchone()
    return jsonify({"user":_ud(user)})

@app.route("/api/auth/profile", methods=["PATCH"])
@auth_required
def update_profile(u):
    d=request.get_json() or {}; db=get_db()
    db.execute("UPDATE users SET name=?,course=?,semester=?,exam=?,daily_goal=? WHERE id=?",
               [d.get("name",u["name"]),d.get("course",""),d.get("semester",1),d.get("exam",""),d.get("daily_goal",6),u["id"]])
    db.commit(); user=db.execute("SELECT * FROM users WHERE id=?",[u["id"]]).fetchone()
    return jsonify({"user":_ud(user)})

def _ud(u): return {k:u[k] for k in ["id","name","email","course","semester","exam","daily_goal","streak","study_days"] if k in u.keys()}

# ── Dashboard ─────────────────────────────────────────────────
@app.route("/api/dashboard")
@auth_required
def dashboard(u):
    db=get_db(); uid=u["id"]; today=str(date.today())
    tasks=db.execute("SELECT * FROM tasks WHERE user_id=? AND date=? ORDER BY id DESC LIMIT 8",[uid,today]).fetchall()
    exams=db.execute("SELECT * FROM exams WHERE user_id=? AND exam_date>=? ORDER BY exam_date LIMIT 5",[uid,today]).fetchall()
    prog=db.execute("SELECT COALESCE(SUM(hours),0) h FROM progress WHERE user_id=? AND date=?",[uid,today]).fetchone()
    topics=db.execute("SELECT t.status FROM topics t JOIN subjects s ON t.subject_id=s.id WHERE s.user_id=?",[uid]).fetchall()
    scores=db.execute("SELECT pct FROM scores WHERE user_id=? ORDER BY id DESC LIMIT 20",[uid]).fetchall()
    streak=_streak(db,uid); done_t=sum(1 for t in topics if t["status"]=="completed"); total_t=len(topics)
    avg_mock=round(sum(s["pct"] for s in scores)/len(scores)) if scores else 0
    exams_data=[{**dict(e),"days_left":(date.fromisoformat(e["exam_date"])-date.today()).days} for e in exams]
    return jsonify({"user":u,"date":today,"tasks":[dict(t) for t in tasks],"exams":exams_data,
                    "hours_today":round(prog["h"] or 0,1),"tasks_total":len(tasks),
                    "tasks_done":sum(1 for t in tasks if t["status"]=="done"),
                    "subject_count":db.execute("SELECT COUNT(*) c FROM subjects WHERE user_id=?",[uid]).fetchone()["c"],
                    "syllabus_pct":round(done_t/total_t*100) if total_t else 0,
                    "streak":streak,"avg_mock":avg_mock,"total_tests":len(scores),
                    "recommendations":_recs(db,uid)})

# ── Subjects ──────────────────────────────────────────────────
@app.route("/api/subjects", methods=["GET"])
@auth_required
def list_subjects(u):
    db=get_db(); subs=db.execute("SELECT * FROM subjects WHERE user_id=? ORDER BY created_at",[u["id"]]).fetchall()
    result=[]
    for s in subs:
        topics=db.execute("SELECT * FROM topics WHERE subject_id=? ORDER BY priority DESC,created_at",[s["id"]]).fetchall()
        result.append({**dict(s),"topics":[{**dict(t),"completed":t["status"]=="completed"} for t in topics]})
    return jsonify({"subjects":result})

@app.route("/api/subjects", methods=["POST"])
@auth_required
def add_subject(u):
    d=request.get_json() or {}; name=d.get("name","").strip()
    if not name: return jsonify({"error":"Subject name required"}),400
    db=get_db(); db.execute("INSERT INTO subjects(user_id,name) VALUES(?,?)",[u["id"],name]); db.commit()
    row=db.execute("SELECT * FROM subjects WHERE user_id=? ORDER BY id DESC LIMIT 1",[u["id"]]).fetchone()
    return jsonify({"message":"Added",**dict(row)}),201

@app.route("/api/subjects/<int:sid>", methods=["DELETE"])
@auth_required
def del_subject(u,sid):
    db=get_db(); db.execute("DELETE FROM subjects WHERE id=? AND user_id=?",[sid,u["id"]]); db.commit()
    return jsonify({"message":"Deleted"})

@app.route("/api/subjects/<int:sid>/topics", methods=["POST"])
@auth_required
def add_topic(u,sid):
    d=request.get_json() or {}; name=d.get("name","").strip()
    if not name: return jsonify({"error":"Topic name required"}),400
    db=get_db()
    if not db.execute("SELECT id FROM subjects WHERE id=? AND user_id=?",[sid,u["id"]]).fetchone():
        return jsonify({"error":"Not found"}),404
    db.execute("INSERT INTO topics(subject_id,name,priority) VALUES(?,?,?)",[sid,name,d.get("priority","Medium")]); db.commit()
    row=db.execute("SELECT * FROM topics WHERE subject_id=? ORDER BY id DESC LIMIT 1",[sid]).fetchone()
    return jsonify({"message":"Added",**dict(row)}),201

@app.route("/api/subjects/topics/<int:tid>", methods=["PATCH"])
@auth_required
def update_topic(u,tid):
    d=request.get_json() or {}; db=get_db()
    for f in ["status","priority","notes","name"]:
        if f in d: db.execute(f"UPDATE topics SET {f}=? WHERE id=?",[d[f],tid])
    db.commit(); return jsonify({"message":"Updated"})

@app.route("/api/subjects/topics/<int:tid>", methods=["DELETE"])
@auth_required
def del_topic(u,tid):
    db=get_db(); db.execute("DELETE FROM topics WHERE id=?",[tid]); db.commit()
    return jsonify({"message":"Deleted"})

# ── Tasks ─────────────────────────────────────────────────────
@app.route("/api/tasks", methods=["GET"])
@auth_required
def get_tasks(u):
    d=request.args.get("date",str(date.today())); db=get_db()
    rows=db.execute("SELECT * FROM tasks WHERE user_id=? AND date=? ORDER BY id DESC",[u["id"],d]).fetchall()
    return jsonify({"tasks":[dict(r) for r in rows],"date":d})

@app.route("/api/tasks", methods=["POST"])
@auth_required
def add_task(u):
    d=request.get_json() or {}
    if not d.get("task","").strip(): return jsonify({"error":"Task required"}),400
    db=get_db()
    db.execute("INSERT INTO tasks(user_id,task,priority,status,date) VALUES(?,?,?,?,?)",
               [u["id"],d["task"].strip(),d.get("priority","Medium"),"pending",d.get("date",str(date.today()))])
    db.commit(); row=db.execute("SELECT * FROM tasks WHERE user_id=? ORDER BY id DESC LIMIT 1",[u["id"]]).fetchone()
    return jsonify({"message":"Created",**dict(row)}),201

@app.route("/api/tasks/<int:tid>", methods=["PATCH"])
@auth_required
def update_task(u,tid):
    d=request.get_json() or {}; db=get_db()
    for f in ["status","task","priority"]:
        if f in d: db.execute(f"UPDATE tasks SET {f}=? WHERE id=? AND user_id=?",[d[f],tid,u["id"]])
    db.commit(); return jsonify({"message":"Updated"})

@app.route("/api/tasks/<int:tid>", methods=["DELETE"])
@auth_required
def del_task(u,tid):
    db=get_db(); db.execute("DELETE FROM tasks WHERE id=? AND user_id=?",[tid,u["id"]]); db.commit()
    return jsonify({"message":"Deleted"})

# ── Exams ─────────────────────────────────────────────────────
@app.route("/api/exams", methods=["GET"])
@auth_required
def get_exams(u):
    db=get_db(); rows=db.execute("SELECT * FROM exams WHERE user_id=? ORDER BY exam_date",[u["id"]]).fetchall()
    return jsonify({"exams":[{**dict(r),"days_left":(date.fromisoformat(r["exam_date"])-date.today()).days} for r in rows]})

@app.route("/api/exams", methods=["POST"])
@auth_required
def add_exam(u):
    d=request.get_json() or {}
    if not d.get("subject") or not d.get("exam_date"): return jsonify({"error":"subject and exam_date required"}),400
    db=get_db(); db.execute("INSERT INTO exams(user_id,subject,exam_date,notes) VALUES(?,?,?,?)",[u["id"],d["subject"],d["exam_date"],d.get("notes","")]); db.commit()
    return jsonify({"message":"Added"}),201

@app.route("/api/exams/<int:eid>", methods=["DELETE"])
@auth_required
def del_exam(u,eid):
    db=get_db(); db.execute("DELETE FROM exams WHERE id=? AND user_id=?",[eid,u["id"]]); db.commit()
    return jsonify({"message":"Deleted"})

# ── Progress ──────────────────────────────────────────────────
@app.route("/api/progress", methods=["GET"])
@auth_required
def get_progress(u):
    db=get_db(); uid=u["id"]; today=str(date.today())
    progs=db.execute("SELECT * FROM progress WHERE user_id=?",[uid]).fetchall()
    subs=db.execute("SELECT * FROM subjects WHERE user_id=?",[uid]).fetchall()
    PALETTE=["#3d5af1","#00c9a7","#ec4899","#f5c842","#10b981","#8b5cf6"]
    DN=["Sun","Mon","Tue","Wed","Thu","Fri","Sat"]
    weekly=[]
    for i in range(6,-1,-1):
        d=date.today()-timedelta(days=i); ds=str(d)
        weekly.append({"label":DN[d.weekday()],"date":ds,"hours":round(sum(p["hours"] for p in progs if p["date"]==ds),1)})
    smap={}
    for p in progs:
        k=p["subject"]
        if k not in smap: smap[k]={"subject":k,"total":0,"days":set()}
        smap[k]["total"]+=p["hours"]; smap[k]["days"].add(p["date"])
    by_subject=[{"subject":v["subject"],"total":round(v["total"],1),"days":len(v["days"])} for v in sorted(smap.values(),key=lambda x:-x["total"])]
    tc=[]
    for i,s in enumerate(subs):
        topics=db.execute("SELECT status FROM topics WHERE subject_id=?",[s["id"]]).fetchall()
        tot=len(topics); done=sum(1 for t in topics if t["status"]=="completed")
        tc.append({"subject":s["name"],"total":tot,"done":done,"pct":round(done/tot*100) if tot else 0,"color":PALETTE[i%len(PALETTE)]})
    study_dates=list({p["date"] for p in progs})
    streak=_streak(db,uid); today_h=sum(p["hours"] for p in progs if p["date"]==today)
    return jsonify({"weekly":weekly,"by_subject":by_subject,"topic_completion":tc,"hours_today":round(today_h,1),"streak":streak,"study_dates":study_dates,"total_hours":round(sum(p["hours"] for p in progs),1)})

@app.route("/api/progress", methods=["POST"])
@auth_required
def log_progress(u):
    d=request.get_json() or {}
    if not d.get("subject") or not d.get("hours"): return jsonify({"error":"subject and hours required"}),400
    db=get_db()
    db.execute("INSERT INTO progress(user_id,subject,hours,notes,date) VALUES(?,?,?,?,?)",
               [u["id"],d["subject"],float(d["hours"]),d.get("notes",""),d.get("date",str(date.today()))])
    db.execute("UPDATE users SET study_days=study_days+1 WHERE id=?",[u["id"]]); db.commit()
    return jsonify({"message":"Logged"}),201

@app.route("/api/analytics", methods=["GET"])
@auth_required
def get_analytics(u):
    db=get_db(); uid=u["id"]
    progs=db.execute("SELECT * FROM progress WHERE user_id=?",[uid]).fetchall()
    scores=db.execute("SELECT * FROM scores WHERE user_id=? ORDER BY id DESC LIMIT 50",[uid]).fetchall()
    topics=db.execute("SELECT t.status FROM topics t JOIN subjects s ON t.subject_id=s.id WHERE s.user_id=?",[uid]).fetchall()
    monthly=[]
    for i in range(29,-1,-1):
        d=date.today()-timedelta(days=i); ds=str(d)
        monthly.append({"date":ds,"hours":round(sum(p["hours"] for p in progs if p["date"]==ds),1)})
    done_t=sum(1 for t in topics if t["status"]=="completed"); total_t=len(topics)
    avg=round(sum(s["pct"] for s in scores)/len(scores)) if scores else 0
    return jsonify({"monthly":monthly,"scores":[dict(s) for s in scores],"total_hours":round(sum(p["hours"] for p in progs),1),"syllabus_pct":round(done_t/total_t*100) if total_t else 0,"total_tests":len(scores),"avg_score":avg,"best_score":max((s["pct"] for s in scores),default=0)})

# ── PYQs ──────────────────────────────────────────────────────
PYQ_SEED=[("Algorithms","GATE",2023,"Graph Algorithms","What is the time complexity of Dijkstra's algorithm using a min-heap?","O((V+E) log V)","Hard",6,95),("Algorithms","GATE",2022,"Sorting","Which sorting algorithm is stable and O(n log n) worst-case?","Merge Sort","Medium",5,88),("Operating Systems","GATE",2023,"Memory Management","Belady's Anomaly is observed in which page replacement algorithm?","FIFO","Medium",5,85),("DBMS","GATE",2023,"Normalization","Which normal form eliminates transitive functional dependencies?","Third Normal Form (3NF)","Medium",8,96),("Computer Networks","GATE",2023,"OSI Model","Which OSI layer handles logical addressing?","Network Layer (Layer 3)","Easy",7,91),("Engineering Physics","University",2023,"Quantum Mechanics","State Heisenberg's Uncertainty Principle.","Δx·Δp ≥ ℏ/2","Medium",4,78),("Polity","UPSC",2023,"Fundamental Rights","Article 32 of the Indian Constitution deals with:","Right to Constitutional Remedies","Medium",7,93),("Physics – Mechanics","JEE",2023,"Projectile Motion","For maximum range, projectile is launched at angle:","45°","Easy",5,84),("Mathematics – Calculus","JEE",2022,"Differentiation","Derivative of xⁿ is:","n·xⁿ⁻¹","Easy",6,87)]

def _seed_pyqs(db):
    if db.execute("SELECT COUNT(*) c FROM pyqs WHERE is_verified=1").fetchone()["c"]==0:
        db.executemany("INSERT INTO pyqs(subject,exam,year,unit,question,answer,difficulty,frequency,importance,is_verified) VALUES(?,?,?,?,?,?,?,?,?,1)",PYQ_SEED); db.commit()

@app.route("/api/pyqs", methods=["GET"])
@auth_required
def get_pyqs(u):
    db=get_db(); _seed_pyqs(db)
    sql="SELECT * FROM pyqs WHERE(is_verified=1 OR user_id=?)"; args=[u["id"]]
    for field,col in [("subject","subject"),("exam","exam"),("year","year"),("diff","difficulty")]:
        v=request.args.get(field)
        if v: sql+=f" AND {col}=?"; args.append(int(v) if field=="year" else v)
    q=request.args.get("q","").lower()
    if q: sql+=" AND(LOWER(question) LIKE ? OR LOWER(subject) LIKE ?)"; args+=[f"%{q}%",f"%{q}%"]
    sql+=" ORDER BY frequency DESC,year DESC"
    rows=db.execute(sql,args).fetchall()
    return jsonify({"pyqs":[dict(r) for r in rows],"total":len(rows)})

@app.route("/api/pyqs", methods=["POST"])
@auth_required
def add_pyq(u):
    d=request.get_json() or {}
    for f in ["subject","exam","year","question","answer"]:
        if not d.get(f): return jsonify({"error":f"{f} required"}),400
    db=get_db()
    db.execute("INSERT INTO pyqs(user_id,subject,exam,year,unit,question,answer,difficulty,frequency,importance) VALUES(?,?,?,?,?,?,?,?,?,?)",
               [u["id"],d["subject"],d["exam"],int(d["year"]),d.get("unit",""),d["question"],d["answer"],d.get("difficulty","Medium"),1,70])
    db.commit(); return jsonify({"message":"Added"}),201

# ── Mock Tests ────────────────────────────────────────────────
MOCK_TESTS=[
    {"id":1,"title":"GATE CS — Full Mock 1","subject":"GATE CS","duration":180,"total_marks":100,"questions":[{"id":1,"text":"Which data structure uses LIFO?","opts":["Queue","Stack","Tree","Graph"],"correct":1,"subj":"Data Structures","marks":2},{"id":2,"text":"Worst-case time complexity of QuickSort?","opts":["O(n log n)","O(n²)","O(n)","O(log n)"],"correct":1,"subj":"Algorithms","marks":2},{"id":3,"text":"Which is NOT a valid SQL command?","opts":["SELECT","UPDATE","REMOVE","DELETE"],"correct":2,"subj":"DBMS","marks":2},{"id":4,"text":"TCP is a ________ protocol.","opts":["Connectionless","Connection-oriented","Broadcast","Multicast"],"correct":1,"subj":"Networks","marks":2},{"id":5,"text":"Which traversal visits BST in ascending order?","opts":["Preorder","Postorder","Inorder","Level-order"],"correct":2,"subj":"Data Structures","marks":2}]},
    {"id":2,"title":"Engineering Physics Quiz","subject":"Engineering Physics","duration":60,"total_marks":20,"questions":[{"id":1,"text":"Speed of light in vacuum?","opts":["3×10⁸ m/s","3×10⁶ m/s","3×10¹⁰ m/s","3×10⁴ m/s"],"correct":0,"subj":"Optics","marks":2},{"id":2,"text":"Which phenomenon proves wave nature of electrons?","opts":["Photoelectric Effect","Electron Diffraction","Compton Effect","Pair Production"],"correct":1,"subj":"Quantum Mechanics","marks":2},{"id":3,"text":"Energy of a photon E =","opts":["mc²","hν","½mv²","qV"],"correct":1,"subj":"Quantum Mechanics","marks":2}]},
    {"id":3,"title":"JEE Mathematics Practice","subject":"JEE","duration":90,"total_marks":20,"questions":[{"id":1,"text":"d/dx(x²) =","opts":["x","2x","2x²","x/2"],"correct":1,"subj":"Calculus","marks":4},{"id":2,"text":"∫cos(x)dx =","opts":["sin(x)+C","-sin(x)+C","tan(x)+C","-cos(x)+C"],"correct":0,"subj":"Calculus","marks":4}]},
    {"id":4,"title":"UPSC GS Practice Set","subject":"UPSC","duration":120,"total_marks":20,"questions":[{"id":1,"text":"Indian Constitution adopted on:","opts":["15 Aug 1947","26 Jan 1950","26 Nov 1949","1 Jan 1950"],"correct":2,"subj":"Polity","marks":2},{"id":2,"text":"Ganga originates from:","opts":["Gangotri","Yamunotri","Kedarnath","Satopanth"],"correct":0,"subj":"Geography","marks":2},{"id":3,"text":"Non-Cooperation Movement started in:","opts":["1919","1920","1921","1922"],"correct":1,"subj":"History","marks":2}]}
]

@app.route("/api/mocktests", methods=["GET"])
@auth_required
def list_tests(u): return jsonify({"tests":MOCK_TESTS})

@app.route("/api/mocktests/<int:tid>", methods=["GET"])
@auth_required
def get_test(u,tid):
    t=next((x for x in MOCK_TESTS if x["id"]==tid),None)
    if not t: return jsonify({"error":"Not found"}),404
    return jsonify({"test":t})

@app.route("/api/mocktests/submit", methods=["POST"])
@auth_required
def submit_test(u):
    d=request.get_json() or {}
    test=next((x for x in MOCK_TESTS if x["id"]==d.get("test_id")),None)
    if not test: return jsonify({"error":"Test not found"}),404
    answers=d.get("answers",{}); time_taken=d.get("time_taken",0)
    correct=wrong=skipped=obtained=0; tmap={}; detailed=[]
    for q in test["questions"]:
        qid=str(q["id"]); ua=answers.get(qid); skip=ua is None or ua==""
        ok=not skip and int(ua)==q["correct"]
        if skip: skipped+=1
        elif ok: correct+=1; obtained+=q["marks"]
        else: wrong+=1
        s=q["subj"]
        if s not in tmap: tmap[s]={"subject":s,"correct":0,"wrong":0,"total":0}
        tmap[s]["total"]+=1
        if ok: tmap[s]["correct"]+=1
        elif not skip: tmap[s]["wrong"]+=1
        detailed.append({**q,"user_answer":int(ua) if ua is not None and ua!="" else None,"is_correct":ok,"skipped":skip})
    tm=sum(q["marks"] for q in test["questions"]); pct=round(obtained/tm*100)
    grade="A" if pct>=80 else "B" if pct>=65 else "C" if pct>=50 else "D"
    db=get_db()
    db.execute("INSERT INTO scores(user_id,test_id,test_title,correct,wrong,skipped,total,obtained,total_marks,pct,time_taken,grade,date) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
               [u["id"],test["id"],test["title"],correct,wrong,skipped,len(test["questions"]),obtained,tm,pct,time_taken,grade,str(date.today())])
    db.commit()
    row=db.execute("SELECT * FROM scores WHERE user_id=? ORDER BY id DESC LIMIT 1",[u["id"]]).fetchone()
    weak=[v for v in tmap.values() if v["total"]>0 and v["correct"]/v["total"]<0.5]
    return jsonify({"score":dict(row),"detailed":detailed,"weak_topics":weak,"grade":grade})

@app.route("/api/scores", methods=["GET"])
@auth_required
def get_scores(u):
    db=get_db(); rows=db.execute("SELECT * FROM scores WHERE user_id=? ORDER BY id DESC LIMIT 50",[u["id"]]).fetchall()
    return jsonify({"scores":[dict(r) for r in rows]})

# ── Planner ───────────────────────────────────────────────────
@app.route("/api/planner/generate", methods=["POST"])
@auth_required
def generate_plan(u):
    d=request.get_json() or {}; exam_date=d.get("exam_date"); daily_hours=int(d.get("daily_hours",6)); mode=d.get("mode","balanced"); subjects=d.get("subjects",[])
    if not exam_date: return jsonify({"error":"exam_date required"}),400
    today=date.today(); exam=date.fromisoformat(exam_date); dl=max(1,(exam-today).days)
    rev=max(1,int(dl*0.2)); sd=dl-rev
    tips=[]; hrs_map={"balanced":daily_hours,"topper":min(daily_hours+2,12),"crash":min(daily_hours+4,12),"weekend":daily_hours,"working":max(daily_hours-1,2)}; hrs=hrs_map.get(mode,daily_hours)
    if dl<=7: tips.append("🚨 Critical: Focus ONLY on revision and past papers.")
    if mode=="crash": tips.append("⚡ Crash mode: High-priority topics and PYQs only.")
    if mode=="topper": tips.append("🏆 Topper mode: Deep coverage + daily mock tests.")
    high=[s for s in subjects if s.get("priority")=="High"]
    if high: tips.append(f"📖 High-priority: {', '.join(s['name'] for s in high)} — schedule mornings.")
    tips.append("💧 5-min break every 50 minutes. Sleep 7-8 hours.")
    DN=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]; days=[]
    for i in range(min(dl,60)):
        d_obj=today+timedelta(days=i); ds=str(d_obj); is_rev=i>=sd
        label=f"{DN[d_obj.weekday()]}, {ds}{' — Revision' if is_rev else ''}"; slots=[]
        if is_rev:
            slots+=[{"start":"09:00","end":"10:30","subject":"Revision Session","type":"revision","tip":"Review all subjects"},{"start":"10:30","end":"10:45","subject":"Break","type":"break","tip":None},{"start":"10:45","end":"12:30","subject":"Past Papers","type":"revision","tip":"PYQ focus"},{"start":"14:00","end":"16:00","subject":"Mock Test","type":"revision","tip":"Full timed test"}]
        else:
            t=8+(2 if mode=="working" else 0)
            for j in range(hrs):
                subj=(subjects[(i*hrs+j)%len(subjects)] if subjects else {"name":"Study","priority":"Medium"})
                slots.append({"start":f"{str(t).zfill(2)}:00","end":f"{str(t+1).zfill(2)}:00","subject":subj["name"],"priority":subj.get("priority","Medium"),"type":"study","tip":"Deep focus" if subj.get("priority")=="High" else None})
                t+=1
                if j==1 and hrs>3: slots.append({"start":f"{str(t).zfill(2)}:00","end":f"{str(t).zfill(2)}:15","subject":"Break","type":"break","tip":None})
            slots.append({"start":f"{str(t).zfill(2)}:00","end":f"{str(t+1).zfill(2)}:00","subject":"Daily Review","type":"revision","tip":"Review today's notes"})
        days.append({"date":ds,"day":i+1,"is_revision":is_rev,"label":label,"slots":slots})
    plan={"exam_date":exam_date,"mode":mode,"daily_hours":hrs,"days_left":dl,"study_days":sd,"revision_days":rev,"tips":tips,"days":days,"created_at":str(date.today())}
    db=get_db(); db.execute("INSERT INTO study_plans(user_id,exam_date,mode,daily_hours,plan_json) VALUES(?,?,?,?,?)",[u["id"],exam_date,mode,hrs,json.dumps(plan)]); db.commit()
    row=db.execute("SELECT id FROM study_plans WHERE user_id=? ORDER BY id DESC LIMIT 1",[u["id"]]).fetchone(); plan["id"]=row["id"]
    db.execute("UPDATE users SET plans_gen=plans_gen+1 WHERE id=?",[u["id"]]); db.commit()
    return jsonify({"plan":plan})

@app.route("/api/planner/saved", methods=["GET"])
@auth_required
def saved_plans(u):
    db=get_db(); rows=db.execute("SELECT * FROM study_plans WHERE user_id=? ORDER BY id DESC LIMIT 10",[u["id"]]).fetchall()
    return jsonify({"plans":[{**json.loads(r["plan_json"]),"id":r["id"]} for r in rows]})

@app.route("/api/planner/<int:pid>", methods=["GET"])
@auth_required
def get_plan(u,pid):
    db=get_db(); row=db.execute("SELECT * FROM study_plans WHERE id=? AND user_id=?",[pid,u["id"]]).fetchone()
    if not row: return jsonify({"error":"Not found"}),404
    return jsonify({"plan":{**json.loads(row["plan_json"]),"id":row["id"]}})

# ── Chat ──────────────────────────────────────────────────────
BOT_R={"greet":["Hi! 👋 I'm StudySaathi AI. Ask me anything about exam prep!"],"gate":["GATE CS: Engg Maths 13%, Algo+DS 15%, DBMS+OS+CN 20%. Last 10 years PYQs are mandatory."],"jee":["JEE tip: NCERT Chemistry is the syllabus. Physics: concepts first. Math: Calculus + Coordinate Geometry = highest weight."],"neet":["NEET: Biology = 50% of marks. Master NCERT Biology line by line. Every diagram matters."],"upsc":["UPSC: NCERT books 6-12 are the foundation. Read The Hindu daily. Answer writing practice is non-negotiable."],"weak":["Weak subject: break into smallest topics → textbook + video → 3 PYQs per topic → spaced repetition every 3 days."],"mock":["Mock test: Spend 2× more time reviewing wrong answers than giving tests. Analyse WHY each was wrong."],"pyq":["PYQ: Start every new topic by reading its PYQs first. ~30% of GATE concepts repeat yearly!"],"motivation":["Remember why you started. Consistency today = rank tomorrow. Study for 25 minutes — START NOW! 💪"],"schedule":["Effective: 50-min focus + 10-min break. Hard subjects in the morning. Revise within 24 hours."],"default":["Ask me about GATE, JEE, NEET, UPSC, study schedules, PYQ tips, or motivation. I'm here to help! 🚀"]}
BOT_K={"greet":["hello","hi","hey"],"gate":["gate"],"jee":["jee","iit"],"neet":["neet","medical"],"upsc":["upsc","ias"],"weak":["weak","difficult","struggling"],"mock":["mock","test strategy"],"pyq":["pyq","previous year"],"motivation":["demotivated","tired","give up","motivation"],"schedule":["schedule","timetable","routine"]}
@app.route("/api/chat", methods=["POST"])
@auth_required
def chat(u):
    msg=(request.get_json() or {}).get("message","").lower()
    for k,kws in BOT_K.items():
        if any(kw in msg for kw in kws):
            r=BOT_R[k]; return jsonify({"reply":r[random.randrange(len(r))],"intent":k})
    return jsonify({"reply":BOT_R["default"][0],"intent":"default"})

# ── Search ────────────────────────────────────────────────────
@app.route("/api/search", methods=["GET"])
@auth_required
def search(u):
    q=(request.args.get("q","")).lower().strip()
    if not q: return jsonify({"results":[]})
    db=get_db(); uid=u["id"]; results=[]
    subs=db.execute("SELECT name FROM subjects WHERE user_id=? AND LOWER(name) LIKE ?",[uid,f"%{q}%"]).fetchall()
    results+=[{"type":"subject","title":s["name"],"sub":"Subject","href":"subjects.html"} for s in subs]
    topics=db.execute("SELECT t.name,s.name subj FROM topics t JOIN subjects s ON t.subject_id=s.id WHERE s.user_id=? AND LOWER(t.name) LIKE ?",[uid,f"%{q}%"]).fetchall()
    results+=[{"type":"topic","title":t["name"],"sub":t["subj"],"href":"subjects.html"} for t in topics]
    pyqs=db.execute("SELECT question,subject,year FROM pyqs WHERE(is_verified=1 OR user_id=?) AND(LOWER(question) LIKE ? OR LOWER(subject) LIKE ?)",[uid,f"%{q}%",f"%{q}%"]).fetchall()
    results+=[{"type":"pyq","title":p["question"][:65]+"…","sub":f"{p['subject']} · {p['year']}","href":"pyq.html"} for p in pyqs[:5]]
    return jsonify({"results":results[:12]})

# ── Achievements ──────────────────────────────────────────────
@app.route("/api/achievements", methods=["GET"])
@auth_required
def get_achievements(u):
    db=get_db(); uid=u["id"]
    usr=db.execute("SELECT * FROM users WHERE id=?",[uid]).fetchone()
    subs=db.execute("SELECT s.id FROM subjects s WHERE s.user_id=?",[uid]).fetchall()
    scores=db.execute("SELECT pct FROM scores WHERE user_id=?",[uid]).fetchall()
    plans=db.execute("SELECT COUNT(*) c FROM study_plans WHERE user_id=?",[uid]).fetchone()
    study_days=db.execute("SELECT COUNT(DISTINCT date) c FROM progress WHERE user_id=?",[uid]).fetchone()
    all_topics=[db.execute("SELECT status FROM topics WHERE subject_id=?",[s["id"]]).fetchall() for s in subs]
    has_complete=any(all(t["status"]=="completed" for t in ts) and ts for ts in all_topics)
    ALIST=[
        {"id":"streak7","icon":"🔥","name":"7-Day Streak","desc":"Study 7 days in a row","unlocked":(usr["streak"] if usr else 0)>=7},
        {"id":"streak30","icon":"⚡","name":"30-Day Streak","desc":"Study 30 days in a row","unlocked":(usr["streak"] if usr else 0)>=30},
        {"id":"subj_master","icon":"📚","name":"Subject Master","desc":"Complete a subject 100%","unlocked":has_complete},
        {"id":"mock_champ","icon":"🏆","name":"Mock Champion","desc":"Score 80%+ in a test","unlocked":any(s["pct"]>=80 for s in scores)},
        {"id":"pyq_expert","icon":"📝","name":"PYQ Expert","desc":"Answer 50+ PYQs","unlocked":(usr["pyq_answered"] if usr else 0)>=50},
        {"id":"first_test","icon":"🧪","name":"First Test","desc":"Complete first mock test","unlocked":len(scores)>0},
        {"id":"planner","icon":"📅","name":"Master Planner","desc":"Generate a study plan","unlocked":(plans["c"] if plans else 0)>0},
        {"id":"consistent","icon":"💎","name":"Consistent Learner","desc":"Log hours for 10 days","unlocked":(study_days["c"] if study_days else 0)>=10},
    ]
    return jsonify({"achievements":ALIST})

# ── Notifications ─────────────────────────────────────────────
@app.route("/api/notifications", methods=["GET"])
@auth_required
def get_notifications(u):
    db=get_db(); uid=u["id"]
    exams=db.execute("SELECT * FROM exams WHERE user_id=? AND exam_date>=?",[uid,str(date.today())]).fetchall()
    notifs=[]; today_h=db.execute("SELECT COALESCE(SUM(hours),0) h FROM progress WHERE user_id=? AND date=?",[uid,str(date.today())]).fetchone()
    for e in exams:
        dl=(date.fromisoformat(e["exam_date"])-date.today()).days
        if dl<=7: notifs.append({"id":e["id"],"type":"exam","icon":"📅","title":f"{e['subject']} in {dl} day(s)!","time":"Now"})
    if today_h["h"]==0: notifs.append({"id":"log","type":"reminder","icon":"⏱","title":"Log today's study hours","time":"Today"})
    return jsonify({"notifications":notifs,"count":len(notifs)})

# ── Helpers ───────────────────────────────────────────────────
def _streak(db,uid):
    rows=db.execute("SELECT DISTINCT date FROM progress WHERE user_id=? ORDER BY date DESC",[uid]).fetchall()
    dates={r["date"] for r in rows}; streak=0; d=date.today()
    for _ in range(60):
        if str(d) in dates: streak+=1
        elif streak>0: break
        d-=timedelta(days=1)
    return streak

def _recs(db,uid):
    r=[]; subs=db.execute("SELECT * FROM subjects WHERE user_id=?",[uid]).fetchall()
    for s in subs:
        topics=db.execute("SELECT status FROM topics WHERE subject_id=?",[s["id"]]).fetchall()
        tot=len(topics); done=sum(1 for t in topics if t["status"]=="completed")
        if tot>0 and done/tot<0.4: r.append({"type":"weak","icon":"📉","title":f"Focus on {s['name']}","msg":f"Only {round(done/tot*100)}% complete."})
    exams=db.execute("SELECT * FROM exams WHERE user_id=? AND exam_date>=?",[uid,str(date.today())]).fetchall()
    for e in exams:
        dl=(date.fromisoformat(e["exam_date"])-date.today()).days
        if 0<=dl<=14: r.append({"type":"exam","icon":"⚠️","title":f"{e['subject']} in {dl} days!","msg":"Switch to intensive revision."})
    last=db.execute("SELECT pct FROM scores WHERE user_id=? ORDER BY id DESC LIMIT 1",[uid]).fetchone()
    if last and last["pct"]<50: r.append({"type":"hard","icon":"📊","title":f"Last mock: {last['pct']}%","msg":"Review wrong answers and revise weak topics."})
    if not r:
        wh=db.execute("SELECT COALESCE(SUM(hours),0) h FROM progress WHERE user_id=? AND date>=?",[uid,str(date.today()-timedelta(days=7))]).fetchone()
        r.append({"type":"good","icon":"🌟","title":f"{round(wh['h'],1)}h this week" if wh["h"] else "Welcome to StudySaathi!","msg":"Great consistency! Keep the streak going." if wh["h"] else "Start adding subjects and logging study hours."})
    return r[:5]

if __name__=="__main__":
    init_db()
    print("🚀 StudySaathi v3 → http://localhost:5000")
    print("📝 Set USE_MOCK=false in core.js to use this backend")
    app.run(debug=True,port=5000)
