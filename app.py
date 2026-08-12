"""
app.py — Flask web server for Study Planner
"""

from flask import Flask, jsonify, request, send_from_directory
import json
import os
import uuid
from datetime import datetime

app = Flask(__name__, static_folder="static", template_folder="static")

# Use absolute path so it works on PythonAnywhere too
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.json")

# ── Persistence ───────────────────────────────────────────────────────────────

def load():
    if not os.path.exists(DATA_FILE):
        return {"subjects": [], "tasks": [], "sessions": []}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"subjects": [], "tasks": [], "sessions": []}


def save(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── Frontend ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


# ── Subjects API ──────────────────────────────────────────────────────────────

@app.route("/api/subjects", methods=["GET"])
def get_subjects():
    return jsonify(load()["subjects"])


@app.route("/api/subjects", methods=["POST"])
def add_subject():
    data = load()
    body = request.get_json()
    name = (body.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Name is required"}), 400
    if any(s["name"].lower() == name.lower() for s in data["subjects"]):
        return jsonify({"error": f'Subject "{name}" already exists'}), 409
    subject = {"subject_id": str(uuid.uuid4())[:8], "name": name}
    data["subjects"].append(subject)
    save(data)
    return jsonify(subject), 201


@app.route("/api/subjects/<subject_id>", methods=["DELETE"])
def delete_subject(subject_id):
    data = load()
    subj = next((s for s in data["subjects"] if s["subject_id"] == subject_id), None)
    if not subj:
        return jsonify({"error": "Subject not found"}), 404
    name = subj["name"]
    data["subjects"] = [s for s in data["subjects"] if s["subject_id"] != subject_id]
    data["tasks"]    = [t for t in data["tasks"]    if t["subject"] != name]
    data["sessions"] = [s for s in data["sessions"] if s["subject"] != name]
    save(data)
    return jsonify({"deleted": subject_id})


# ── Tasks API ─────────────────────────────────────────────────────────────────

@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    data = load()
    tasks = data["tasks"]
    # optional filter params
    subject = request.args.get("subject")
    status  = request.args.get("status")
    if subject:
        tasks = [t for t in tasks if t["subject"] == subject]
    if status:
        tasks = [t for t in tasks if t["status"] == status]
    # attach overdue flag
    today = datetime.today().date()
    for t in tasks:
        try:
            due = datetime.strptime(t["due_date"], "%Y-%m-%d").date()
            t["overdue"] = (due < today and t["status"] != "Completed")
        except ValueError:
            t["overdue"] = False
    return jsonify(tasks)


@app.route("/api/tasks", methods=["POST"])
def add_task():
    data = load()
    body = request.get_json()
    title   = (body.get("title") or "").strip()
    subject = (body.get("subject") or "").strip()
    due     = (body.get("due_date") or "").strip()
    priority = body.get("priority", "Medium")
    notes    = (body.get("notes") or "").strip()

    if not title:
        return jsonify({"error": "Title is required"}), 400
    if not subject:
        return jsonify({"error": "Subject is required"}), 400
    if not due:
        return jsonify({"error": "Due date is required"}), 400
    try:
        datetime.strptime(due, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Invalid date format (YYYY-MM-DD)"}), 400
    if priority not in ("High", "Medium", "Low"):
        priority = "Medium"

    task = {
        "task_id":    str(uuid.uuid4())[:8],
        "title":      title,
        "subject":    subject,
        "due_date":   due,
        "priority":   priority,
        "status":     "Pending",
        "notes":      notes,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    data["tasks"].append(task)
    save(data)
    return jsonify(task), 201


@app.route("/api/tasks/<task_id>", methods=["PATCH"])
def update_task(task_id):
    data = load()
    task = next((t for t in data["tasks"] if t["task_id"] == task_id), None)
    if not task:
        return jsonify({"error": "Task not found"}), 404

    body = request.get_json()
    for field in ("title", "subject", "due_date", "priority", "status", "notes"):
        if field in body:
            task[field] = body[field]

    save(data)
    return jsonify(task)


@app.route("/api/tasks/<task_id>", methods=["DELETE"])
def delete_task(task_id):
    data = load()
    task = next((t for t in data["tasks"] if t["task_id"] == task_id), None)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    data["tasks"] = [t for t in data["tasks"] if t["task_id"] != task_id]
    save(data)
    return jsonify({"deleted": task_id})


# ── Sessions API ──────────────────────────────────────────────────────────────

@app.route("/api/sessions", methods=["GET"])
def get_sessions():
    data = load()
    sessions = data["sessions"]
    subject = request.args.get("subject")
    if subject:
        sessions = [s for s in sessions if s["subject"] == subject]
    sessions.sort(key=lambda s: s["date"], reverse=True)
    return jsonify(sessions)


@app.route("/api/sessions", methods=["POST"])
def add_session():
    data = load()
    body = request.get_json()
    subject  = (body.get("subject") or "").strip()
    date     = (body.get("date") or "").strip()
    duration = body.get("duration_minutes")
    notes    = (body.get("notes") or "").strip()

    if not subject:
        return jsonify({"error": "Subject is required"}), 400
    if not date:
        return jsonify({"error": "Date is required"}), 400
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Invalid date (YYYY-MM-DD)"}), 400
    if not isinstance(duration, int) or duration <= 0:
        return jsonify({"error": "Duration must be a positive integer"}), 400

    session = {
        "session_id":       str(uuid.uuid4())[:8],
        "subject":          subject,
        "date":             date,
        "duration_minutes": duration,
        "notes":            notes,
    }
    data["sessions"].append(session)
    save(data)
    return jsonify(session), 201


@app.route("/api/sessions/<session_id>", methods=["DELETE"])
def delete_session(session_id):
    data = load()
    session = next((s for s in data["sessions"] if s["session_id"] == session_id), None)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    data["sessions"] = [s for s in data["sessions"] if s["session_id"] != session_id]
    save(data)
    return jsonify({"deleted": session_id})


# ── Progress API ──────────────────────────────────────────────────────────────

@app.route("/api/progress", methods=["GET"])
def get_progress():
    data = load()
    today = datetime.today().date()
    result = []
    for subj in data["subjects"]:
        name = subj["name"]
        subj_tasks = [t for t in data["tasks"] if t["subject"] == name]
        total   = len(subj_tasks)
        done    = sum(1 for t in subj_tasks if t["status"] == "Completed")
        inprog  = sum(1 for t in subj_tasks if t["status"] == "In Progress")
        overdue = 0
        for t in subj_tasks:
            try:
                due = datetime.strptime(t["due_date"], "%Y-%m-%d").date()
                if due < today and t["status"] != "Completed":
                    overdue += 1
            except ValueError:
                pass
        mins = sum(s["duration_minutes"] for s in data["sessions"] if s["subject"] == name)
        pct  = int((done / total) * 100) if total else 0
        result.append({
            "name":    name,
            "total":   total,
            "done":    done,
            "inprog":  inprog,
            "overdue": overdue,
            "minutes": mins,
            "percent": pct,
        })
    return jsonify(result)


if __name__ == "__main__":
    print("Study Planner running at http://127.0.0.1:5000")
    app.run(debug=False, port=5000)
