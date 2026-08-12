# 📖 Study Planner

A fully-featured command-line study planner built in Python.

## Features

| Feature | Details |
|---|---|
| **Subject management** | Add and remove subjects |
| **Task management** | Add tasks with title, subject, due date, priority, and notes |
| **Task filtering** | View all / by subject / today / this week / overdue / by status |
| **Task updates** | Edit title, due date, priority, status, notes |
| **Mark complete** | Quickly mark tasks as done |
| **Study sessions** | Log study sessions with duration |
| **Session filtering** | View all / by subject / today / this week |
| **Progress overview** | Per-subject progress bar, stats, and total study time |
| **Persistent storage** | All data saved to `data.json` automatically |
| **Coloured CLI** | ANSI-coloured interface with overdue/priority highlights |

## Requirements

- Python 3.10+ (uses `X | None` union syntax)
- No third-party packages required

## Running

```bash
cd study_planner
python main.py
```

## Project Structure

```
study_planner/
├── main.py       # CLI entry point and all menu actions
├── models.py     # Task, Subject, StudySession dataclasses
├── storage.py    # JSON load/save
├── display.py    # ANSI-coloured print helpers
├── data.json     # Auto-created on first run
└── README.md
```

## Usage

1. **Add a subject** first (e.g. "Mathematics", "History")
2. **Add tasks** under that subject with a due date and priority
3. **Log study sessions** to track time spent
4. **Check progress** for a per-subject overview
