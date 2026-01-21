from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from . import lesson_tracking

PATH_MODELING_GEOMETRY_NODES = "modeling.geometry_nodes"

TOPIC_KEY_SEP = "::"
LESSON_ID_PREFIX = "topic::"

# Derived from Blender50Manual HTML tree (blender_manual_v500_en.html/modeling/geometry_nodes).
_GEOMETRY_NODES_TOPICS = [
    "attribute",
    "color",
    "curve",
    "generate",
    "geometry",
    "grease_pencil",
    "hair",
    "input",
    "instances",
    "mesh",
    "normals",
    "output",
    "point",
    "simulation",
    "texture",
    "utilities",
    "volume",
]

LEARNING_PATHS: Dict[str, Dict[str, object]] = {
    PATH_MODELING_GEOMETRY_NODES: {
        "category": "Modeling",
        "label": "Geometry Nodes",
        "manual_path": "modeling/geometry_nodes",
        "topics": _GEOMETRY_NODES_TOPICS,
    },
}


def humanize_slug(slug: str) -> str:
    return slug.replace("_", " ").replace("-", " ").title()


def path_label(path_id: str) -> str:
    data = LEARNING_PATHS.get(path_id)
    if not data:
        return path_id
    category = str(data.get("category", ""))
    label = str(data.get("label", path_id))
    if category:
        return f"{category} > {label}"
    return label


def get_enabled_paths(prefs) -> List[str]:
    paths: List[str] = []
    if getattr(prefs, "enable_path_modeling_geometry_nodes", False):
        paths.append(PATH_MODELING_GEOMETRY_NODES)
    return paths


def make_topic_key(path_id: str, slug: str) -> str:
    return f"{path_id}{TOPIC_KEY_SEP}{slug}"


def split_topic_key(topic_key: str) -> Tuple[Optional[str], Optional[str]]:
    if TOPIC_KEY_SEP not in topic_key:
        return None, None
    path_id, slug = topic_key.split(TOPIC_KEY_SEP, 1)
    return path_id, slug


def lesson_id_for_topic(topic_key: str) -> str:
    return f"{LESSON_ID_PREFIX}{topic_key}"


def is_topic_lesson_id(lesson_id: str) -> bool:
    return lesson_id.startswith(LESSON_ID_PREFIX)


def topic_key_from_lesson_id(lesson_id: str) -> Optional[str]:
    if not is_topic_lesson_id(lesson_id):
        return None
    return lesson_id[len(LESSON_ID_PREFIX) :]


def topic_label(slug: str) -> str:
    return humanize_slug(slug)


def topics_for_path(path_id: str) -> List[str]:
    data = LEARNING_PATHS.get(path_id)
    if not data:
        return []
    topics = data.get("topics", [])
    return [str(item) for item in topics]


def available_topic_keys(path_id: str) -> List[str]:
    topics = topics_for_path(path_id)
    completed = lesson_tracking.get_completed_topics()
    available: List[str] = []
    for slug in topics:
        key = make_topic_key(path_id, slug)
        if key not in completed:
            available.append(key)
    return available


def learning_path_items(self, context):
    if context is None:
        return [("NONE", "No context", "No Blender context")]
    addon = context.preferences.addons.get(__package__)
    if not addon:
        return [("NONE", "No preferences", "Add-on preferences unavailable")]
    enabled = get_enabled_paths(addon.preferences)
    if not enabled:
        return [("NONE", "No Learning Paths", "Enable learning paths in Preferences")]
    return [(path_id, path_label(path_id), path_label(path_id)) for path_id in enabled]


def topic_items(self, context):
    if context is None:
        return [("NONE", "No context", "No Blender context")]
    wm = context.window_manager
    path_id = wm.chiron_active_learning_path
    if not path_id or path_id == "NONE":
        return [("NONE", "Select a Learning Path", "Choose a learning path first")]
    available = available_topic_keys(path_id)
    if not available:
        return [("NONE", "No topics available", "All topics completed")]
    items = []
    for key in available:
        _, slug = split_topic_key(key)
        if not slug:
            continue
        items.append((key, topic_label(slug), ""))
    return items or [("NONE", "No topics available", "All topics completed")]
