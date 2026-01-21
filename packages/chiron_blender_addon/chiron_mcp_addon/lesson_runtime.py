from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Callable, Dict, List, Optional

import bpy

from . import learning_paths

@dataclass
class LessonStep:
    step_id: str
    title: str
    instruction: str
    hint: str
    validator: Callable[[], bool]
    show_me: Optional[Callable[[], None]] = None
    ui_diagram: Optional[Dict[str, object]] = None


DEFAULT_LESSON_ID = "core_basics_demo"
PACK_CACHE: Dict[str, List["LessonStep"]] = {}


def _ensure_object_mode():
    try:
        if bpy.context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
    except Exception:
        return


def _get_cube():
    return bpy.data.objects.get("Cube")


def _is_cube_selected() -> bool:
    cube = _get_cube()
    if not cube:
        return False
    return cube.select_get() and bpy.context.view_layer.objects.active == cube


def _is_cube_moved_x() -> bool:
    cube = _get_cube()
    if not cube:
        return False
    return abs(cube.location.x) > 0.01


def _has_second_mesh() -> bool:
    mesh_count = len([obj for obj in bpy.context.scene.objects if obj.type == "MESH"])
    return mesh_count >= 2


def _show_select_cube():
    _ensure_object_mode()
    bpy.ops.object.select_all(action="DESELECT")
    cube = _get_cube()
    if cube:
        cube.select_set(True)
        bpy.context.view_layer.objects.active = cube


def _show_move_cube():
    _ensure_object_mode()
    cube = _get_cube()
    if cube:
        cube.location.x = 1.0


def _show_add_mesh():
    _ensure_object_mode()
    try:
        bpy.ops.mesh.primitive_uv_sphere_add(location=(2.0, 0.0, 0.0))
    except Exception:
        bpy.ops.mesh.primitive_cube_add(location=(2.0, 0.0, 0.0))


_DEFAULT_STEPS: List[LessonStep] = [
    LessonStep(
        step_id="select-cube",
        title="Select the cube",
        instruction="Select the default Cube object.",
        hint="Click the Cube in the viewport or select it in the Outliner.",
        validator=_is_cube_selected,
        show_me=_show_select_cube,
        ui_diagram={
            "type": "ui_diagram",
            "editor": "OUTLINER",
            "tab": "Scene Collection",
            "callout": "Select the Cube",
            "breadcrumbs": ["Outliner", "Scene Collection", "Cube"],
        },
    ),
    LessonStep(
        step_id="move-cube-x",
        title="Move the cube on X",
        instruction="Move the Cube along the X axis.",
        hint="Press G then X, then move the mouse and click to confirm.",
        validator=_is_cube_moved_x,
        show_me=_show_move_cube,
    ),
    LessonStep(
        step_id="add-mesh",
        title="Add a second mesh",
        instruction="Add a new mesh object to the scene.",
        hint="Use Add -> Mesh -> UV Sphere.",
        validator=_has_second_mesh,
        show_me=_show_add_mesh,
        ui_diagram={
            "type": "ui_diagram",
            "editor": "VIEW_3D",
            "tab": "Add",
            "callout": "Add a mesh",
            "breadcrumbs": ["3D Viewport", "Add", "Mesh", "UV Sphere"],
        },
    ),
]


def _always_true() -> bool:
    return True


def _topic_steps_for(topic_key: str) -> Optional[List[LessonStep]]:
    path_id, slug = learning_paths.split_topic_key(topic_key)
    if not path_id or not slug:
        return None
    topic_label = learning_paths.topic_label(slug)
    hint = "Click Next when you are ready to continue."
    return [
        LessonStep(
            step_id="open-editor",
            title="Open Geometry Nodes",
            instruction="Open the Geometry Nodes editor.",
            hint=hint,
            validator=_always_true,
        ),
        LessonStep(
            step_id="review-topic",
            title=f"Review: {topic_label}",
            instruction=f"Review the {topic_label} section in the Blender Manual.",
            hint=hint,
            validator=_always_true,
        ),
        LessonStep(
            step_id="apply-topic",
            title=f"Apply: {topic_label}",
            instruction=f"Apply one change using {topic_label} nodes in your scene.",
            hint=hint,
            validator=_always_true,
        ),
    ]


def _topic_steps_from_lesson_id(lesson_id: str) -> Optional[List[LessonStep]]:
    topic_key = learning_paths.topic_key_from_lesson_id(lesson_id)
    if not topic_key:
        return None
    return _topic_steps_for(topic_key)


def build_steps_from_source(lesson: Dict[str, object]) -> List[LessonStep]:
    steps_data = lesson.get("steps", [])
    steps: List[LessonStep] = []
    for index, item in enumerate(steps_data):
        try:
            step_id = str(item.get("step_id", f"step-{index + 1}"))
            title = str(item.get("title", f"Step {index + 1}"))
            instruction = str(item.get("instruction", ""))
            hint = str(item.get("hint", "")) or "Complete the step and click Next."
            steps.append(
                LessonStep(
                    step_id=step_id,
                    title=title,
                    instruction=instruction,
                    hint=hint,
                    validator=_always_true,
                )
            )
        except Exception:
            continue
    return steps


def set_steps(lesson_id: str, steps: List[LessonStep]):
    if not lesson_id:
        return
    PACK_CACHE[lesson_id] = steps


def _validator_object_exists(args: Dict[str, object]) -> bool:
    name = str(args.get("name", ""))
    if not name:
        return False
    return bpy.data.objects.get(name) is not None


def _validator_object_selected(args: Dict[str, object]) -> bool:
    name = str(args.get("name", ""))
    obj = bpy.data.objects.get(name)
    if not obj:
        return False
    return obj.select_get() and bpy.context.view_layer.objects.active == obj


def _validator_object_moved_axis(args: Dict[str, object]) -> bool:
    name = str(args.get("name", ""))
    axis = str(args.get("axis", "X")).upper()
    min_abs = float(args.get("min_abs", 0.01))
    obj = bpy.data.objects.get(name)
    if not obj:
        return False
    value = getattr(obj.location, axis.lower(), 0.0)
    return abs(float(value)) > min_abs


def _validator_mesh_count_at_least(args: Dict[str, object]) -> bool:
    count = int(args.get("count", 1))
    mesh_count = len([obj for obj in bpy.context.scene.objects if obj.type == "MESH"])
    return mesh_count >= count


def _validator_object_has_modifier(args: Dict[str, object]) -> bool:
    name = str(args.get("name", ""))
    modifier = str(args.get("modifier", ""))
    obj = bpy.data.objects.get(name)
    if not obj:
        return False
    return any(mod.name == modifier for mod in obj.modifiers)


VALIDATORS: Dict[str, Callable[[Dict[str, object]], bool]] = {
    "object_exists": _validator_object_exists,
    "object_selected": _validator_object_selected,
    "object_moved_axis": _validator_object_moved_axis,
    "mesh_count_at_least": _validator_mesh_count_at_least,
    "object_has_modifier": _validator_object_has_modifier,
}


def _make_validator(name: str, args: Dict[str, object]) -> Callable[[], bool]:
    def _runner():
        func = VALIDATORS.get(name)
        if not func:
            return False
        return func(args)

    return _runner


def _addon_dir() -> str:
    return os.path.dirname(__file__)


def _lesson_pack_path(lesson_id: str) -> str:
    return os.path.join(_addon_dir(), "lesson_packs", f"{lesson_id}.json")


def _load_pack_from_disk(lesson_id: str) -> Optional[List[LessonStep]]:
    path = _lesson_pack_path(lesson_id)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except Exception:
        return None
    steps_data = payload.get("steps", [])
    steps: List[LessonStep] = []
    for item in steps_data:
        try:
            validator_spec = item.get("validator", {})
            validator_name = str(validator_spec.get("name", ""))
            validator_args = dict(validator_spec.get("args", {}))
            step = LessonStep(
                step_id=str(item.get("step_id", "")),
                title=str(item.get("title", "")),
                instruction=str(item.get("instruction", "")),
                hint=str(item.get("hint", "")),
                validator=_make_validator(validator_name, validator_args),
                show_me=None,
                ui_diagram=item.get("ui_diagram"),
            )
            steps.append(step)
        except Exception:
            continue
    return steps or None


def load_lesson_steps(lesson_id: str) -> List[LessonStep]:
    if lesson_id in PACK_CACHE:
        return PACK_CACHE[lesson_id]
    steps = _load_pack_from_disk(lesson_id)
    if steps is None:
        steps = _DEFAULT_STEPS
    PACK_CACHE[lesson_id] = steps
    return steps


def get_lesson_steps(lesson_id: str) -> List[LessonStep]:
    if lesson_id in PACK_CACHE:
        return PACK_CACHE[lesson_id]
    if learning_paths.is_topic_lesson_id(lesson_id):
        steps = _topic_steps_from_lesson_id(lesson_id)
        if steps:
            PACK_CACHE[lesson_id] = steps
            return steps
    return load_lesson_steps(lesson_id)


def get_step(lesson_id: str, index: int) -> Optional[LessonStep]:
    steps = get_lesson_steps(lesson_id)
    if index < 0 or index >= len(steps):
        return None
    return steps[index]


def validate_step(lesson_id: str, index: int) -> bool:
    step = get_step(lesson_id, index)
    if not step:
        return False
    try:
        return bool(step.validator())
    except Exception:
        return False


def run_show_me(lesson_id: str, index: int) -> bool:
    step = get_step(lesson_id, index)
    if not step or not step.show_me:
        return False
    try:
        step.show_me()
        return True
    except Exception:
        return False


def _progress_path() -> str:
    base = bpy.utils.user_resource("CONFIG", "chiron", create=True)
    return os.path.join(base, "progress.json")


def save_progress(
    lesson_id: str,
    step_index: int,
    learning_path_id: Optional[str] = None,
    topic_key: Optional[str] = None,
    source_url: Optional[str] = None,
):
    payload = {"lesson_id": lesson_id, "step_index": step_index}
    if learning_path_id:
        payload["learning_path_id"] = learning_path_id
    if topic_key:
        payload["topic_key"] = topic_key
    if source_url:
        payload["source_url"] = source_url
    try:
        with open(_progress_path(), "w", encoding="utf-8") as handle:
            json.dump(payload, handle)
    except Exception:
        return


def load_progress() -> Dict[str, object]:
    try:
        with open(_progress_path(), "r", encoding="utf-8") as handle:
            payload = json.load(handle)
            if isinstance(payload, dict):
                return payload
    except Exception:
        return {}
    return {}


def load_progress_into_wm(wm):
    payload = load_progress()
    lesson_id = payload.get("lesson_id")
    step_index = payload.get("step_index")
    learning_path_id = payload.get("learning_path_id")
    topic_key = payload.get("topic_key")
    source_url = payload.get("source_url")
    if isinstance(lesson_id, str) and lesson_id:
        wm.chiron_lesson_id = lesson_id
    if isinstance(step_index, int) and step_index >= 0:
        wm.chiron_step_index = step_index
    if isinstance(learning_path_id, str) and learning_path_id:
        wm.chiron_active_learning_path = learning_path_id
    if isinstance(topic_key, str) and topic_key:
        wm.chiron_active_topic = topic_key
        wm.chiron_current_topic_key = topic_key
    if isinstance(source_url, str) and source_url:
        wm.chiron_source_url = source_url
