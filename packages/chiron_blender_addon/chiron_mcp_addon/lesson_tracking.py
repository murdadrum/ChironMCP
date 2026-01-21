from __future__ import annotations

import json
import os
from typing import Dict, List, Set

import bpy

_HISTORY_FILENAME = "lesson_history.json"


def _history_path() -> str:
    base = bpy.utils.user_resource("CONFIG", "chiron", create=True)
    return os.path.join(base, _HISTORY_FILENAME)


def load_history() -> Dict[str, List[str]]:
    try:
        with open(_history_path(), "r", encoding="utf-8") as handle:
            payload = json.load(handle)
            if isinstance(payload, dict):
                completed = payload.get("completed_topics", [])
                if isinstance(completed, list):
                    return {"completed_topics": [str(item) for item in completed]}
    except Exception:
        return {"completed_topics": []}
    return {"completed_topics": []}


def save_history(history: Dict[str, List[str]]):
    try:
        with open(_history_path(), "w", encoding="utf-8") as handle:
            json.dump(history, handle)
    except Exception:
        return


def get_completed_topics() -> Set[str]:
    history = load_history()
    completed = history.get("completed_topics", [])
    return set(completed)


def mark_topic_completed(topic_key: str) -> bool:
    if not topic_key:
        return False
    history = load_history()
    completed = history.get("completed_topics", [])
    if topic_key in completed:
        return False
    completed.append(topic_key)
    history["completed_topics"] = completed
    save_history(history)
    return True


def reset_history():
    save_history({"completed_topics": []})
