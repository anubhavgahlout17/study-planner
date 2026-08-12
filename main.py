"""
main.py — Entry point for Study Planner CLI
"""

import os
import sys
from datetime import datetime, timedelta
from typing import List, Optional

from models import Task, Subject, StudySession, PRIORITIES, STATUSES
from storage import load_data, save_data
from display import (
    header, success, error, info,
    print_subjects, print_tasks, print_sessions, print_progress,
    BOLD, RESET, CYAN, YELLOW, WHITE, BLUE, GREEN, RED, GREY,
)

# ── State ────────────────────────────────────────────────────────────────────
subjects: List[Subject] = []
tasks: List[Task] = []
sessions: List[StudySession] = []


# ── Helpers ──────────────────────────────────────────────────────────────────
def _save():
    save_data(subjects, tasks, sessions)


def _clear():
    os.system("cls" if os.name == "nt" else "clear")


def _prompt(msg: str, default: str = "") -> str:
    val = input(f"  {CYAN}{msg}{RESET} ").strip()
    return val if val else default


def _pick_subject(prompt_msg: str = "Subject name") -> str:
    """Show numbered subject list and let user pick by number or type name."""
    if not subjects:
        error("No subjects exist. Please add one first.")
        return ""
    print_subjects(subjects)
    raw = _prompt(f"{prompt_msg} (number or name):")
    if raw.isdigit():
        idx = int(raw) - 1
        if 0 <= idx < len(subjects):
            return subjects[idx].name
        error("Invalid number.")
        return ""
    # Match by name (case-insensitive)
    for s in subjects:
        if s.name.lower() == raw.lower():
            return s.name
    error(f'Subject "{raw}" not found.')
    return ""


def _validate_date(date_str: str) -> bool:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def _pick_priority() -> str:
    print(f"  Priority: {RED}1) High{RESET}  {YELLOW}2) Medium{RESET}  {GREEN}3) Low{RESET}")
    raw = _prompt("Choose (1/2/3):", "2")
    return PRIORITIES.get(raw, "Medium")


def _pick_status() -> str:
    for i, s in enumerate(STATUSES, 1):
        print(f"  {i}) {s}")
    raw = _prompt(f"Status (1-{len(STATUSES)}):", "1")
    if raw.isdigit() and 1 <= int(raw) <= len(STATUSES):
        return STATUSES[int(raw) - 1]
    return "Pending"


def _find_task(task_id: str) -> "Optional[Task]":
    for t in tasks:
        if t.task_id == task_id:
            return t
    return None


def _today_str() -> str:
    return datetime.today().strftime("%Y-%m-%d")


# ── Subject actions ──────────────────────────────────────────────────────────
def add_subject():
    header("Add Subject")
    name = _prompt("Subject name:")
    if not name:
        error("Name cannot be empty.")
        return
    if any(s.name.lower() == name.lower() for s in subjects):
        error(f'Subject "{name}" already exists.')
        return
    subjects.append(Subject(name=name))
    _save()
    success(f'Subject "{name}" added.')


def remove_subject():
    global subjects, tasks, sessions
    header("Remove Subject")
    print_subjects(subjects)
    if not subjects:
        return
    raw = _prompt("Subject number or name to remove:")
    name = ""
    if raw.isdigit():
        idx = int(raw) - 1
        if 0 <= idx < len(subjects):
            name = subjects[idx].name
    else:
        for s in subjects:
            if s.name.lower() == raw.lower():
                name = s.name
                break
    if not name:
        error("Subject not found.")
        return
    confirm = _prompt(f'Delete "{name}" and ALL its tasks? (yes/no):').lower()
    if confirm != "yes":
        info("Cancelled.")
        return
    subjects = [s for s in subjects if s.name != name]
    tasks    = [t for t in tasks    if t.subject != name]
    sessions = [s for s in sessions if s.subject != name]
    _save()
    success(f'Subject "{name}" removed.')


# ── Task actions ─────────────────────────────────────────────────────────────
def add_task():
    header("Add Task")
    subject = _pick_subject("Select subject:")
    if not subject:
        return
    title = _prompt("Task title:")
    if not title:
        error("Title cannot be empty.")
        return
    while True:
        due = _prompt(f"Due date (YYYY-MM-DD) [today={_today_str()}]:", _today_str())
        if _validate_date(due):
            break
        error("Invalid date format. Use YYYY-MM-DD.")
    priority = _pick_priority()
    notes = _prompt("Notes (optional):")
    task = Task(title=title, subject=subject, due_date=due, priority=priority, notes=notes)
    tasks.append(task)
    _save()
    success(f'Task "{title}" added under "{subject}".')


def view_tasks():
    header("View Tasks")
    print(f"  Filter by:  {CYAN}1) All  2) Subject  3) Today  4) This Week  5) Overdue  6) By Status{RESET}")
    choice = _prompt("Choice:", "1")

    filtered = list(tasks)
    title = "All Tasks"

    if choice == "2":
        subj = _pick_subject()
        if not subj:
            return
        filtered = [t for t in tasks if t.subject == subj]
        title = f"Tasks — {subj}"
    elif choice == "3":
        today = _today_str()
        filtered = [t for t in tasks if t.due_date == today]
        title = f"Tasks due Today ({today})"
    elif choice == "4":
        today = datetime.today().date()
        end   = today + timedelta(days=6)
        filtered = [
            t for t in tasks
            if _validate_date(t.due_date)
            and today <= datetime.strptime(t.due_date, "%Y-%m-%d").date() <= end
        ]
        title = "Tasks due This Week"
    elif choice == "5":
        filtered = [t for t in tasks if t.is_overdue()]
        title = "Overdue Tasks"
    elif choice == "6":
        status = _pick_status()
        filtered = [t for t in tasks if t.status == status]
        title = f"Tasks — {status}"

    # Sort: overdue first, then by due date, then by priority weight
    prio_w = {"High": 0, "Medium": 1, "Low": 2}
    filtered.sort(key=lambda t: (
        not t.is_overdue(),
        t.due_date,
        prio_w.get(t.priority, 1),
    ))
    print_tasks(filtered, title)


def update_task():
    header("Update Task")
    view_tasks()
    if not tasks:
        return
    task_id = _prompt("Enter Task ID to update:")
    task = _find_task(task_id)
    if not task:
        error(f"Task ID '{task_id}' not found.")
        return

    print(f"\n  Editing: {BOLD}{task.title}{RESET}  ({task.subject})")
    print(f"  Leave blank to keep current value.\n")

    new_title = _prompt(f"Title [{task.title}]:")
    if new_title:
        task.title = new_title

    new_due = _prompt(f"Due date [{task.due_date}]:")
    if new_due:
        if _validate_date(new_due):
            task.due_date = new_due
        else:
            error("Invalid date — keeping original.")

    print(f"  Current priority: {task.priority}")
    change_p = _prompt("Change priority? (y/n):").lower()
    if change_p == "y":
        task.priority = _pick_priority()

    print(f"  Current status: {task.status}")
    change_s = _prompt("Change status? (y/n):").lower()
    if change_s == "y":
        task.status = _pick_status()

    new_notes = _prompt(f"Notes [{task.notes or 'none'}]:")
    if new_notes:
        task.notes = new_notes

    _save()
    success(f'Task "{task.title}" updated.')


def delete_task():
    header("Delete Task")
    view_tasks()
    if not tasks:
        return
    task_id = _prompt("Enter Task ID to delete:")
    task = _find_task(task_id)
    if not task:
        error(f"Task ID '{task_id}' not found.")
        return
    confirm = _prompt(f'Delete "{task.title}"? (yes/no):').lower()
    if confirm != "yes":
        info("Cancelled.")
        return
    tasks.remove(task)
    _save()
    success(f'Task "{task.title}" deleted.')


def mark_complete():
    header("Mark Task Complete")
    pending = [t for t in tasks if t.status != "Completed"]
    print_tasks(pending, "Incomplete Tasks")
    if not pending:
        return
    task_id = _prompt("Enter Task ID to mark complete:")
    task = _find_task(task_id)
    if not task:
        error(f"Task ID '{task_id}' not found.")
        return
    task.status = "Completed"
    _save()
    success(f'"{task.title}" marked as Completed!')


# ── Study Session actions ─────────────────────────────────────────────────────
def log_session():
    header("Log Study Session")
    subject = _pick_subject()
    if not subject:
        return
    date = _prompt(f"Date (YYYY-MM-DD) [today={_today_str()}]:", _today_str())
    if not _validate_date(date):
        error("Invalid date.")
        return
    raw_mins = _prompt("Duration (minutes):", "60")
    if not raw_mins.isdigit() or int(raw_mins) <= 0:
        error("Duration must be a positive integer.")
        return
    notes = _prompt("Notes (optional):")
    session = StudySession(subject=subject, date=date, duration_minutes=int(raw_mins), notes=notes)
    sessions.append(session)
    _save()
    success(f"Logged {raw_mins} min of {subject} on {date}.")


def view_sessions():
    header("View Sessions")
    print(f"  Filter:  {CYAN}1) All  2) By Subject  3) Today  4) This Week{RESET}")
    choice = _prompt("Choice:", "1")
    filtered = list(sessions)
    title = "All Study Sessions"
    if choice == "2":
        subj = _pick_subject()
        if not subj:
            return
        filtered = [s for s in sessions if s.subject == subj]
        title = f"Sessions - {subj}"
    elif choice == "3":
        filtered = [s for s in sessions if s.date == _today_str()]
        title = "Today's Sessions"
    elif choice == "4":
        today = datetime.today().date()
        end   = today + timedelta(days=6)
        filtered = [
            s for s in sessions
            if _validate_date(s.date)
            and today <= datetime.strptime(s.date, "%Y-%m-%d").date() <= end
        ]
        title = "This Week's Sessions"
    filtered.sort(key=lambda s: s.date, reverse=True)
    print_sessions(filtered)


# ── Progress ──────────────────────────────────────────────────────────────────
def show_progress():
    print_progress(subjects, tasks, sessions)


# ── Main menu ─────────────────────────────────────────────────────────────────
MENU = [
    ("--- SUBJECTS -----------------------------------", None),
    ("Add Subject",    add_subject),
    ("Remove Subject", remove_subject),
    ("--- TASKS -------------------------------------", None),
    ("Add Task",       add_task),
    ("View Tasks",     view_tasks),
    ("Update Task",    update_task),
    ("Mark Complete",  mark_complete),
    ("Delete Task",    delete_task),
    ("--- STUDY SESSIONS ----------------------------", None),
    ("Log Study Session", log_session),
    ("View Sessions",     view_sessions),
    ("--- OVERVIEW ----------------------------------", None),
    ("Progress Overview", show_progress),
    ("------------------------------------------------", None),
    ("Exit",           None),
]


def _build_menu() -> list:
    """Return (display_label, index, fn) only for selectable items."""
    items = []
    idx = 1
    for label, fn in MENU:
        if fn is not None:
            items.append((idx, label, fn))
            idx += 1
        elif label.startswith("Exit"):
            items.append((idx, label, None))
            idx += 1
    return items


def print_menu(selectable: list) -> None:
    _clear()
    print(f"\n{BOLD}{BLUE}+================================================+{RESET}")
    print(f"{BOLD}{BLUE}|           ** STUDY PLANNER **                  |{RESET}")
    print(f"{BOLD}{BLUE}+================================================+{RESET}\n")

    sel_iter = iter(selectable)
    current = next(sel_iter, None)

    for label, fn in MENU:
        if fn is None and not label.startswith("Exit"):
            # Section header
            print(f"  {GREY}{label}{RESET}")
        elif fn is not None or label.startswith("Exit"):
            if current and current[1] == label:
                num, lbl, _ = current
                print(f"  {CYAN}{num:>2}.{RESET} {WHITE}{lbl}{RESET}")
                current = next(sel_iter, None)
        else:
            print(f"  {GREY}{label}{RESET}")

    print()


def main():
    global subjects, tasks, sessions
    data = load_data()
    subjects = data["subjects"]
    tasks    = data["tasks"]
    sessions = data["sessions"]

    selectable = _build_menu()
    max_choice = selectable[-1][0]

    while True:
        print_menu(selectable)
        # Show quick stats
        total_tasks = len(tasks)
        done_tasks  = sum(1 for t in tasks if t.status == "Completed")
        overdue     = sum(1 for t in tasks if t.is_overdue())
        today_tasks = [t for t in tasks if t.due_date == _today_str() and t.status != "Completed"]
        print(f"  {GREY}Tasks: {total_tasks}  Done: {done_tasks}  Overdue: {overdue}  |  Due today: {len(today_tasks)}{RESET}\n")

        raw = _prompt(f"Choose (1-{max_choice}):")
        if not raw.isdigit():
            continue
        choice = int(raw)

        # Find matching item
        match = next((item for item in selectable if item[0] == choice), None)
        if not match:
            error(f"Invalid choice. Enter 1-{max_choice}.")
            input(f"  {GREY}Press Enter to continue...{RESET}")
            continue

        _, label, fn = match
        if label == "Exit":
            print(f"\n{GREEN}Goodbye! Keep studying! 📚{RESET}\n")
            sys.exit(0)

        fn()
        input(f"\n  {GREY}Press Enter to continue...{RESET}")


if __name__ == "__main__":
    main()
