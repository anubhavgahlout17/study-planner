# 📚 Study Planner

A fully-featured **Study Planner web application** built with **Python + Streamlit**.

Track subjects, manage tasks, log study sessions, and monitor your progress — all in a clean, interactive browser UI.

---

## ✨ Features

| Feature | Details |
|---|---|
| **Dashboard** | Live stats, motivational quote, overdue/today tasks, SVG progress ring, recent activity |
| **Subject management** | Add and remove subjects (with cascade delete of related tasks & sessions) |
| **Task management** | Add tasks with title, subject, due date, priority, status, and notes |
| **Task filtering** | Filter by status (All / Pending / In Progress / Completed / Overdue), subject, and time range (Today / This Week) |
| **Task updates** | Edit title, due date, priority, status, and notes inline |
| **Mark complete** | One-click toggle to mark tasks as completed or reopen them |
| **Study sessions** | Log study sessions with subject, date, duration, and notes |
| **Session filtering** | Filter session history by subject |
| **Progress overview** | Per-subject progress bars, completion %, task stats, and total study time |
| **Persistent storage** | All data saved automatically to `data.json` |

---

## 🛠 Tech Stack

- **Python 3.10+**
- **Streamlit** — UI framework
- **JSON** — local file-based data storage (no database required)

---

## 🚀 Running Locally

### 1. Clone the repository

```bash
git clone https://github.com/anubhavgahlout17/study-planner.git
cd study-planner
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the app

```bash
streamlit run app.py
```

The app opens automatically at **http://localhost:8501**

---

## 📁 Project Structure

```
study-planner/
├── app.py            # ★ Main Streamlit application (entry point)
├── models.py         # Task, Subject, StudySession dataclasses
├── storage.py        # JSON load/save helpers (legacy CLI support)
├── display.py        # ANSI console helpers (legacy CLI support)
├── main.py           # Legacy CLI entry point (no longer the main UI)
├── data.json         # Auto-created persistent data store
├── requirements.txt  # Python dependencies
├── render.yaml       # Render deployment config
└── README.md
```

---

## ☁️ Deploying to Render

The project is ready for [Render](https://render.com) deployment via `render.yaml`.

**Build command:**
```bash
pip install -r requirements.txt
```

**Start command:**
```bash
streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
```

The `RENDER=true` environment variable is set automatically — when running on Render, data is written to `/tmp/study_planner_data.json` (writable path).

---

## 📖 Usage Guide

1. **Add a Subject** — Go to **Subjects** → expand "Add New Subject" → enter a name
2. **Add a Task** — Go to **Tasks** → expand "Add New Task" → fill in title, subject, due date, priority
3. **Edit / Complete / Delete a Task** — Each task row has ✏️ Edit, ✅ Complete, 🗑️ Delete buttons
4. **Log a Study Session** — Go to **Study Sessions** → expand "Log New Session" → pick subject, date, duration
5. **Track Progress** — Go to **Progress** for per-subject completion stats and study time
6. **Dashboard** — Shows today's tasks, overdue tasks, recent sessions, and overall progress ring

---

## 📦 Requirements

```
streamlit>=1.35.0
```

No additional packages required.
