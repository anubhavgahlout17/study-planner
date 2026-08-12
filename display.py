"""
display.py — Console formatting helpers for Study Planner
"""

from datetime import datetime
from typing import List
from models import Task, Subject, StudySession


# ── ANSI color codes ────────────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
CYAN   = "\033[96m"
GREY   = "\033[90m"
WHITE  = "\033[97m"


def _priority_color(priority: str) -> str:
    return {
        "High":   RED,
        "Medium": YELLOW,
        "Low":    GREEN,
    }.get(priority, WHITE)


def _status_color(status: str) -> str:
    return {
        "Pending":     GREY,
        "In Progress": CYAN,
        "Completed":   GREEN,
    }.get(status, WHITE)


def header(text: str) -> None:
    width = 60
    print(f"\n{BOLD}{BLUE}{'-' * width}{RESET}")
    print(f"{BOLD}{BLUE}  {text}{RESET}")
    print(f"{BOLD}{BLUE}{'-' * width}{RESET}")


def success(msg: str) -> None:
    print(f"{GREEN}[OK]  {msg}{RESET}")


def error(msg: str) -> None:
    print(f"{RED}[ERR] {msg}{RESET}")


def info(msg: str) -> None:
    print(f"{CYAN}[i]   {msg}{RESET}")


def print_subjects(subjects: List[Subject]) -> None:
    header("Subjects")
    if not subjects:
        info("No subjects added yet.")
        return
    for i, s in enumerate(subjects, 1):
        print(f"  {BOLD}{i}.{RESET} {WHITE}{s.name}{RESET}  {GREY}(ID: {s.subject_id}){RESET}")


def print_tasks(tasks: List[Task], title: str = "Tasks") -> None:
    header(title)
    if not tasks:
        info("No tasks found.")
        return

    for t in tasks:
        overdue_tag = f" {RED}[OVERDUE]{RESET}" if t.is_overdue() else ""
        pc = _priority_color(t.priority)
        sc = _status_color(t.status)
        print(
            f"  {BOLD}{GREY}[{t.task_id}]{RESET} "
            f"{WHITE}{t.title}{RESET}"
            f"  {BLUE}({t.subject}){RESET}"
            f"  {pc}[{t.priority}]{RESET}"
            f"  {sc}{t.status}{RESET}"
            f"  Due: {t.due_date_display()}"
            f"{overdue_tag}"
        )
        if t.notes:
            print(f"          {GREY}Notes: {t.notes}{RESET}")


def print_sessions(sessions: List[StudySession]) -> None:
    header("Study Sessions")
    if not sessions:
        info("No sessions logged yet.")
        return
    total = sum(s.duration_minutes for s in sessions)
    for s in sessions:
        print(
            f"  {GREY}[{s.session_id}]{RESET} "
            f"{WHITE}{s.subject}{RESET}"
            f"  Date: {s.date}"
            f"  Time: {s.duration_minutes} min"
            + (f"  {GREY}| {s.notes}{RESET}" if s.notes else "")
        )
    print(f"\n  {BOLD}Total study time: {total // 60}h {total % 60}m{RESET}")


def print_progress(subjects: List[Subject], tasks: List[Task], sessions: List[StudySession]) -> None:
    header("Progress Overview")
    if not subjects:
        info("No subjects added yet.")
        return
    for subj in subjects:
        subj_tasks = [t for t in tasks if t.subject == subj.name]
        total   = len(subj_tasks)
        done    = sum(1 for t in subj_tasks if t.status == "Completed")
        inprog  = sum(1 for t in subj_tasks if t.status == "In Progress")
        overdue = sum(1 for t in subj_tasks if t.is_overdue())
        mins    = sum(s.duration_minutes for s in sessions if s.subject == subj.name)
        pct     = int((done / total) * 100) if total else 0
        bar     = _progress_bar(pct)
        print(
            f"\n  {BOLD}{WHITE}{subj.name}{RESET}\n"
            f"    Tasks: {total}  Done: {done}  In Progress: {inprog}  Overdue: {overdue}\n"
            f"    {bar} {pct}%\n"
            f"    Study time: {mins // 60}h {mins % 60}m"
        )


def _progress_bar(pct: int, width: int = 20) -> str:
    filled = int(width * pct / 100)
    bar = "#" * filled + "." * (width - filled)
    color = GREEN if pct >= 75 else YELLOW if pct >= 40 else RED
    return f"{color}[{bar}]{RESET}"
