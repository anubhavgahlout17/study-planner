"""
storage.py — JSON-based persistence for Study Planner
"""

import json
import os
from typing import List

from models import Task, Subject, StudySession

DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")


def _default_data() -> dict:
    return {"subjects": [], "tasks": [], "sessions": []}


def load_data() -> dict:
    """Load all data from JSON file. Returns default structure if file missing."""
    if not os.path.exists(DATA_FILE):
        return _default_data()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return {
            "subjects": [Subject.from_dict(s) for s in raw.get("subjects", [])],
            "tasks": [Task.from_dict(t) for t in raw.get("tasks", [])],
            "sessions": [StudySession.from_dict(s) for s in raw.get("sessions", [])],
        }
    except (json.JSONDecodeError, KeyError):
        print("[Warning] data.json is corrupted. Starting fresh.")
        return _default_data()


def save_data(subjects: List[Subject], tasks: List[Task], sessions: List[StudySession]) -> None:
    """Persist all data to JSON file."""
    payload = {
        "subjects": [s.to_dict() for s in subjects],
        "tasks": [t.to_dict() for t in tasks],
        "sessions": [s.to_dict() for s in sessions],
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
