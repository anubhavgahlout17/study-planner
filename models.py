"""
models.py — Data models for Study Planner
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


PRIORITIES = {"1": "High", "2": "Medium", "3": "Low"}
STATUSES = ["Pending", "In Progress", "Completed"]


@dataclass
class Task:
    title: str
    subject: str
    due_date: str          # ISO format: YYYY-MM-DD
    priority: str          # High | Medium | Low
    status: str = "Pending"
    notes: str = ""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "subject": self.subject,
            "due_date": self.due_date,
            "priority": self.priority,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at,
        }

    @staticmethod
    def from_dict(d: dict) -> "Task":
        return Task(
            task_id=d["task_id"],
            title=d["title"],
            subject=d["subject"],
            due_date=d["due_date"],
            priority=d["priority"],
            status=d.get("status", "Pending"),
            notes=d.get("notes", ""),
            created_at=d.get("created_at", ""),
        )

    def is_overdue(self) -> bool:
        if self.status == "Completed":
            return False
        try:
            return datetime.strptime(self.due_date, "%Y-%m-%d").date() < datetime.today().date()
        except ValueError:
            return False

    def due_date_display(self) -> str:
        try:
            dt = datetime.strptime(self.due_date, "%Y-%m-%d")
            return dt.strftime("%d %b %Y")
        except ValueError:
            return self.due_date


@dataclass
class Subject:
    name: str
    color: str = "white"   # for future UI use
    subject_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def to_dict(self) -> dict:
        return {
            "subject_id": self.subject_id,
            "name": self.name,
            "color": self.color,
        }

    @staticmethod
    def from_dict(d: dict) -> "Subject":
        return Subject(
            subject_id=d["subject_id"],
            name=d["name"],
            color=d.get("color", "white"),
        )


@dataclass
class StudySession:
    subject: str
    date: str              # YYYY-MM-DD
    duration_minutes: int
    notes: str = ""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "subject": self.subject,
            "date": self.date,
            "duration_minutes": self.duration_minutes,
            "notes": self.notes,
        }

    @staticmethod
    def from_dict(d: dict) -> "StudySession":
        return StudySession(
            session_id=d["session_id"],
            subject=d["subject"],
            date=d["date"],
            duration_minutes=d["duration_minutes"],
            notes=d.get("notes", ""),
        )
