import base64
import hashlib
import json
import os
import tempfile
import time
import urllib.request

import bpy
import blf
import gpu
from gpu_extras.batch import batch_for_shader

from . import learning_paths, lesson_runtime, lesson_tracking

try:
    import bgl  # Blender < 4.x
except Exception:
    bgl = None

DEFAULT_MCP_HTTP = "http://localhost:8000"
_DRAW_HANDLES = []
_TOAST_MESSAGE = ""
_TOAST_EXPIRES = 0.0
_HIGHLIGHT_TARGET = ""
_HIGHLIGHT_EXPIRES = 0.0
_OVERLAY_TICK = 0.1
_TIMER_ACTIVE = False
_DEBUG_OVERLAY = False
_DEBUG_EXPIRES = 0.0
_CHAT_HISTORY_LIMIT = 12
_HTTP_TIMEOUT = 20
_CHAT_ACTIONS = ("toast", "highlight")

SUPPORTED_SPACES = (
    bpy.types.SpaceView3D,
    bpy.types.SpaceProperties,
    bpy.types.SpaceOutliner,
    bpy.types.SpaceNodeEditor,
    bpy.types.SpacePreferences,
    bpy.types.SpaceConsole,
    bpy.types.SpaceInfo,
)
SUPPORTED_REGIONS = ("WINDOW", "HEADER", "TOOLS", "UI")


def _now() -> float:
    return time.time()


def _tag_redraw():
    wm = bpy.context.window_manager
    for window in wm.windows:
        for area in window.screen.areas:
            area.tag_redraw()


def _ensure_draw_handler():
    global _DRAW_HANDLES
    if _DRAW_HANDLES:
        return
    for space_type in SUPPORTED_SPACES:
        for region_type in SUPPORTED_REGIONS:
            try:
                handle = space_type.draw_handler_add(
                    _draw_callback_px,
                    (),
                    region_type,
                    "POST_PIXEL",
                )
                _DRAW_HANDLES.append((space_type, region_type, handle))
            except Exception:
                continue


def _remove_draw_handler():
    global _DRAW_HANDLES
    for space_type, region_type, handle in _DRAW_HANDLES:
        try:
            space_type.draw_handler_remove(handle, region_type)
        except Exception:
            continue
    _DRAW_HANDLES = []


def _overlay_tick():
    global _TOAST_MESSAGE, _HIGHLIGHT_TARGET, _TIMER_ACTIVE, _DEBUG_OVERLAY
    now = _now()
    if _TOAST_MESSAGE and now > _TOAST_EXPIRES:
        _TOAST_MESSAGE = ""
    if _HIGHLIGHT_TARGET and now > _HIGHLIGHT_EXPIRES:
        _HIGHLIGHT_TARGET = ""
    if _DEBUG_OVERLAY and now > _DEBUG_EXPIRES:
        _DEBUG_OVERLAY = False

    if not _TOAST_MESSAGE and not _HIGHLIGHT_TARGET and not _DEBUG_OVERLAY:
        _TIMER_ACTIVE = False
        return None

    _tag_redraw()
    return _OVERLAY_TICK


def _schedule_overlay_tick():
    global _TIMER_ACTIVE
    if _TIMER_ACTIVE:
        return
    _TIMER_ACTIVE = True
    bpy.app.timers.register(_overlay_tick, first_interval=_OVERLAY_TICK)


def _show_toast(message: str, duration: float = 2.5):
    global _TOAST_MESSAGE, _TOAST_EXPIRES
    _TOAST_MESSAGE = message
    _TOAST_EXPIRES = _now() + duration
    _ensure_draw_handler()
    _schedule_overlay_tick()
    _tag_redraw()
    bpy.ops.wm.redraw_timer(type="DRAW_WIN_SWAP", iterations=1)


def _show_highlight(target: str, duration: float = 2.5):
    global _HIGHLIGHT_TARGET, _HIGHLIGHT_EXPIRES
    _HIGHLIGHT_TARGET = target
    _HIGHLIGHT_EXPIRES = _now() + duration
    _ensure_draw_handler()
    _schedule_overlay_tick()
    _tag_redraw()
    bpy.ops.wm.redraw_timer(type="DRAW_WIN_SWAP", iterations=1)


def _show_debug_overlay(duration: float = 3.0):
    global _DEBUG_OVERLAY, _DEBUG_EXPIRES
    _DEBUG_OVERLAY = True
    _DEBUG_EXPIRES = _now() + duration
    _ensure_draw_handler()
    _schedule_overlay_tick()
    _tag_redraw()


def _parse_highlight_target(target: str):
    if not target:
        return None, None
    if ":" in target:
        area_part, region_part = target.split(":", 1)
        return area_part.strip().upper(), region_part.strip().upper()
    region_only = {"TOOLS", "UI", "HEADER", "WINDOW"}
    if target.upper() in region_only:
        return None, target.upper()
    return target.upper(), "WINDOW"


def _diagram_spec_for_step(step):
    if not step:
        return None
    return step.ui_diagram


def _diagram_cache_path(spec: dict) -> str:
    spec_json = json.dumps(spec, sort_keys=True)
    digest = hashlib.sha256(spec_json.encode("utf-8")).hexdigest()[:12]
    temp_dir = bpy.app.tempdir or tempfile.gettempdir()
    return os.path.join(temp_dir, f"chiron_diagram_{digest}.png")


def _fetch_diagram(spec: dict):
    try:
        response = _http_post(f"{DEFAULT_MCP_HTTP}/ui/diagram", spec)
    except Exception:
        return None
    if not response.get("ok"):
        return None
    b64 = response.get("image_base64")
    if not b64:
        return None
    try:
        data = base64.b64decode(b64)
    except Exception:
        return None
    path = _diagram_cache_path(spec)
    try:
        with open(path, "wb") as handle:
            handle.write(data)
        image = bpy.data.images.load(path, check_existing=True)
        return image.name
    except Exception:
        return None


def _update_diagram_for_current_step(wm) -> bool:
    lesson_id = _get_lesson_id(wm)
    step = lesson_runtime.get_step(lesson_id, wm.chiron_step_index)
    spec = _diagram_spec_for_step(step)
    if not spec:
        wm.chiron_diagram_image = ""
        wm.chiron_diagram_status = "No diagram for this step"
        return False
    image_name = _fetch_diagram(spec)
    if image_name:
        wm.chiron_diagram_image = image_name
        wm.chiron_diagram_status = "Diagram updated"
        return True
    wm.chiron_diagram_status = "Diagram fetch failed"
    return False


def ensure_overlay_handler():
    _ensure_draw_handler()


def remove_overlay_handler():
    _remove_draw_handler()


def _draw_rect_filled(x, y, w, h, color):
    shader = gpu.shader.from_builtin("2D_UNIFORM_COLOR")
    verts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    batch = batch_for_shader(shader, "TRI_FAN", {"pos": verts})
    if hasattr(gpu.state, "blend_set"):
        gpu.state.blend_set("ALPHA")
    if hasattr(gpu.state, "depth_test_set"):
        gpu.state.depth_test_set("NONE")
    if hasattr(gpu.state, "face_culling_set"):
        gpu.state.face_culling_set("NONE")
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)
    if hasattr(gpu.state, "blend_set"):
        gpu.state.blend_set("NONE")
    if bgl is not None:
        _draw_rect_filled_bgl(x, y, w, h, color)


def _draw_rect_outline(x, y, w, h, color, width=2):
    shader = gpu.shader.from_builtin("2D_UNIFORM_COLOR")
    verts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]
    batch = batch_for_shader(shader, "LINE_STRIP", {"pos": verts})
    if hasattr(gpu.state, "line_width_set"):
        gpu.state.line_width_set(width)
    if hasattr(gpu.state, "depth_test_set"):
        gpu.state.depth_test_set("NONE")
    if hasattr(gpu.state, "face_culling_set"):
        gpu.state.face_culling_set("NONE")
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)
    if hasattr(gpu.state, "line_width_set"):
        gpu.state.line_width_set(1)
    if bgl is not None:
        _draw_rect_outline_bgl(x, y, w, h, color, width=width)


def _draw_rect_filled_bgl(x, y, w, h, color):
    if bgl is None:
        return
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glColor4f(*color)
    bgl.glBegin(bgl.GL_QUADS)
    bgl.glVertex2f(x, y)
    bgl.glVertex2f(x + w, y)
    bgl.glVertex2f(x + w, y + h)
    bgl.glVertex2f(x, y + h)
    bgl.glEnd()
    bgl.glDisable(bgl.GL_BLEND)


def _draw_rect_outline_bgl(x, y, w, h, color, width=2):
    if bgl is None:
        return
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glColor4f(*color)
    bgl.glLineWidth(width)
    bgl.glBegin(bgl.GL_LINE_LOOP)
    bgl.glVertex2f(x, y)
    bgl.glVertex2f(x + w, y)
    bgl.glVertex2f(x + w, y + h)
    bgl.glVertex2f(x, y + h)
    bgl.glEnd()
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)


def _draw_text(text, x, y, size=14, color=(1, 1, 1, 1)):
    font_id = 0
    blf.position(font_id, x, y, 0)
    try:
        blf.size(font_id, size, 72)
    except TypeError:
        blf.size(font_id, size)
    blf.color(font_id, *color)
    blf.draw(font_id, text)


def _draw_callback_px():
    try:
        region = bpy.context.region
        area = bpy.context.area
    except Exception:
        region = None
        area = None

    if region is None or area is None:
        return

    w = region.width
    h = region.height
    draw_toast = False
    draw_highlight = False
    if _TOAST_MESSAGE:
        draw_toast = area.type == "VIEW_3D" and region.type == "WINDOW"
    if _HIGHLIGHT_TARGET:
        target_area, target_region = _parse_highlight_target(_HIGHLIGHT_TARGET)
        if target_area and area.type != target_area:
            draw_highlight = False
        elif target_region and region.type != target_region:
            draw_highlight = False
        else:
            draw_highlight = True

    if draw_toast:
        padding = 10
        box_w = min(520, w - 2 * padding)
        box_h = 30
        x = padding
        y = h - box_h - padding
        _draw_rect_filled(x, y, box_w, box_h, (0.1, 0.5, 0.1, 0.9))
        _draw_text(_TOAST_MESSAGE, x + 8, y + 8, size=14, color=(1, 1, 1, 1))

    if draw_highlight:
        margin = 6
        _draw_rect_outline(margin, margin, w - margin * 2, h - margin * 2, (1, 0.2, 0.2, 1), width=4)
        _draw_text(f"Highlight: {_HIGHLIGHT_TARGET}", margin + 8, margin + 12, size=12, color=(1, 0.2, 0.2, 1))

    if _DEBUG_OVERLAY:
        _draw_rect_filled(0, 0, w, h, (0.6, 0.0, 0.6, 0.12))
        _draw_text("CHIRON OVERLAY ACTIVE", 20, 20, size=18, color=(1, 0.2, 0.2, 1))
        area_type = area.type if area else "None"
        _draw_text(f"AREA {area_type} REGION {region.type} {w}x{h}", 20, 42, size=12, color=(1, 1, 0.2, 1))
        if _TOAST_MESSAGE:
            _draw_text(f"TOAST: {_TOAST_MESSAGE}", 20, 62, size=12, color=(0.2, 1, 0.2, 1))


def _http_post(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url=url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _http_get(url: str) -> dict:
    req = urllib.request.Request(
        url=url,
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _server_url() -> str:
    addon = bpy.context.preferences.addons.get(__package__)
    prefs = addon.preferences if addon else None
    if prefs:
        server_url = getattr(prefs, "server_url", "").strip()
        if server_url:
            return server_url.rstrip("/")
    env_url = os.environ.get("CHIRON_MCP_URL", "").strip()
    if env_url:
        return env_url.rstrip("/")
    return DEFAULT_MCP_HTTP.rstrip("/")


def _normalize_model_name(model: str) -> str:
    name = model.strip()
    if name == "chatgpt-5.2":
        return "gpt-5.2"
    return name


class CHIRON_OT_ping_server(bpy.types.Operator):
    bl_idname = "chiron.ping_server"
    bl_label = "Ping Server"
    bl_description = "Ping the local Chiron MCP server"

    def execute(self, context):
        wm = context.window_manager
        try:
            response = _http_get(f"{_server_url()}/health")
            if response.get("ok"):
                status = response.get("status", "ok")
                wm.chiron_server_ok = True
                wm.chiron_server_status = status
                self.report({"INFO"}, f"Server OK: {status}")
            else:
                wm.chiron_server_ok = False
                wm.chiron_server_status = "Unhealthy"
                self.report({"ERROR"}, f"Server unhealthy: {response}")
            return {"FINISHED"}
        except Exception as e:
            wm.chiron_server_ok = False
            wm.chiron_server_status = "Unavailable"
            self.report({"ERROR"}, f"Server unavailable: {e}")
            return {"CANCELLED"}


class CHIRON_OT_send_toast(bpy.types.Operator):
    bl_idname = "chiron.send_toast"
    bl_label = "Send Toast"
    bl_description = "Send a toast message to the MCP server"

    def execute(self, context):
        wm = context.window_manager
        try:
            payload = {"message": wm.chiron_toast_message, "level": "INFO"}
            response = _http_post(f"{_server_url()}/blender/toast", payload)
            if response.get("ok"):
                _show_toast(response.get("message", "Toast sent"))
                _show_debug_overlay()
                self.report({"INFO"}, f"Toast sent: {response.get('message', '')}")
                return {"FINISHED"}
            self.report({"ERROR"}, f"Toast failed: {response}")
            return {"CANCELLED"}
        except Exception as e:
            self.report({"ERROR"}, f"Toast error: {e}")
            return {"CANCELLED"}


class CHIRON_OT_send_highlight(bpy.types.Operator):
    bl_idname = "chiron.send_highlight"
    bl_label = "Send Highlight"
    bl_description = "Send a highlight target to the MCP server"

    def execute(self, context):
        wm = context.window_manager
        try:
            payload = {"target": wm.chiron_highlight_target}
            response = _http_post(f"{_server_url()}/blender/highlight", payload)
            if response.get("ok"):
                _show_highlight(response.get("target", "Highlight"))
                _show_debug_overlay()
                self.report({"INFO"}, f"Highlight sent: {response.get('target', '')}")
                return {"FINISHED"}
            self.report({"ERROR"}, f"Highlight failed: {response}")
            return {"CANCELLED"}
        except Exception as e:
            self.report({"ERROR"}, f"Highlight error: {e}")
            return {"CANCELLED"}


def _get_lesson_id(wm) -> str:
    return wm.chiron_lesson_id or lesson_runtime.DEFAULT_LESSON_ID


def _set_status(wm, message: str):
    wm.chiron_step_status = message


def _set_topic_status(wm, message: str):
    wm.chiron_topic_status = message


def _set_source_status(wm, message: str):
    wm.chiron_source_status = message


def _set_chat_status(wm, message: str):
    wm.chiron_chat_status = message


def _collect_blender_context():
    context = {}
    try:
        scene = bpy.context.scene
        context["scene_name"] = scene.name
        context["object_count"] = len(scene.objects)
        context["frame_current"] = scene.frame_current
    except Exception:
        pass
    try:
        view_layer = bpy.context.view_layer
        active = view_layer.objects.active
        context["active_object"] = active.name if active else ""
        selected = list(bpy.context.selected_objects or [])
        context["selected_count"] = len(selected)
        context["selected_objects"] = [obj.name for obj in selected[:20]]
    except Exception:
        pass
    try:
        context["mode"] = bpy.context.mode
    except Exception:
        pass
    return context


def _apply_chat_actions(wm, actions):
    if not isinstance(actions, list):
        return
    for action in actions:
        if not isinstance(action, dict):
            continue
        action_type = str(action.get("type", "")).strip().lower()
        if action_type not in _CHAT_ACTIONS:
            continue
        if action_type == "toast":
            message = str(action.get("message", "")).strip()
            if message:
                _show_toast(message)
        elif action_type == "highlight":
            target = str(action.get("target", "")).strip()
            if target:
                _show_highlight(target)


def _load_chat_history(wm):
    raw = wm.chiron_chat_history.strip()
    if not raw:
        return []
    try:
        history = json.loads(raw)
    except Exception:
        return []
    return history if isinstance(history, list) else []


def _save_chat_history(wm, history):
    if len(history) > _CHAT_HISTORY_LIMIT:
        history = history[-_CHAT_HISTORY_LIMIT:]
    wm.chiron_chat_history = json.dumps(history)
    return history


def _append_chat_history(wm, role: str, content: str):
    if not content:
        return _load_chat_history(wm)
    history = _load_chat_history(wm)
    history.append({"role": role, "content": content})
    return _save_chat_history(wm, history)


def _save_progress(wm):
    learning_path_id = wm.chiron_active_learning_path
    if learning_path_id == "NONE":
        learning_path_id = ""
    lesson_runtime.save_progress(
        wm.chiron_lesson_id,
        wm.chiron_step_index,
        learning_path_id=learning_path_id,
        topic_key=wm.chiron_current_topic_key,
        source_url=wm.chiron_source_url,
    )


class CHIRON_OT_diagram_fetch(bpy.types.Operator):
    bl_idname = "chiron.diagram_fetch"
    bl_label = "Refresh Diagram"
    bl_description = "Fetch the UI diagram for the current step"

    def execute(self, context):
        wm = context.window_manager
        ok = _update_diagram_for_current_step(wm)
        if ok:
            self.report({"INFO"}, "Diagram updated")
            return {"FINISHED"}
        self.report({"WARNING"}, wm.chiron_diagram_status)
        return {"CANCELLED"}


def _source_lesson_id(url: str) -> str:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
    return f"source::{digest}"


class CHIRON_OT_source_generate(bpy.types.Operator):
    bl_idname = "chiron.source_generate"
    bl_label = "Generate From Source"
    bl_description = "Generate a lesson from a tutorial source URL"

    def execute(self, context):
        wm = context.window_manager
        url = wm.chiron_source_url.strip()
        if not url:
            _set_source_status(wm, "Enter a source URL")
            self.report({"WARNING"}, "Enter a source URL")
            return {"CANCELLED"}
        if not (url.startswith("http://") or url.startswith("https://")):
            _set_source_status(wm, "URL must start with http:// or https://")
            self.report({"WARNING"}, "URL must start with http:// or https://")
            return {"CANCELLED"}
        try:
            response = _http_post(
                f"{_server_url()}/tutorial/source",
                {"url": url, "use_llm": bool(wm.chiron_source_use_llm)},
            )
        except Exception as e:
            _set_source_status(wm, "Source fetch failed")
            self.report({"ERROR"}, f"Source fetch failed: {e}")
            return {"CANCELLED"}
        if not response.get("ok"):
            status = response.get("status")
            error = response.get("error")
            if error == "fetch_timeout":
                message = "Source fetch failed: timed out"
            elif status and isinstance(status, int):
                message = f"Source fetch failed (HTTP {status})"
            else:
                message = error or "Source fetch failed"
            _set_source_status(wm, message)
            self.report({"ERROR"}, message)
            return {"CANCELLED"}
        lesson = response.get("lesson", {})
        steps = lesson_runtime.build_steps_from_source(lesson)
        if not steps:
            _set_source_status(wm, "No steps found")
            self.report({"WARNING"}, "No steps found in source")
            return {"CANCELLED"}
        lesson_id = _source_lesson_id(url)
        lesson_runtime.set_steps(lesson_id, steps)
        wm.chiron_lesson_id = lesson_id
        wm.chiron_step_index = 0
        wm.chiron_step_hint = ""
        wm.chiron_current_topic_key = ""
        _set_status(wm, "In progress")
        title = lesson.get("title", "Source lesson")
        if response.get("llm_used"):
            _set_source_status(wm, f"LLM loaded: {title}")
        else:
            error = response.get("llm_error")
            if error == "llm_not_configured":
                _set_source_status(wm, f"Loaded (LLM not configured): {title}")
            elif error == "llm_failed":
                _set_source_status(wm, f"Loaded (LLM failed): {title}")
            else:
                _set_source_status(wm, f"Loaded: {title}")
        _save_progress(wm)
        self.report({"INFO"}, "Lesson generated from source")
        return {"FINISHED"}


class CHIRON_OT_chat_send(bpy.types.Operator):
    bl_idname = "chiron.chat_send"
    bl_label = "Send"
    bl_description = "Send a prompt to the Chiron chat"

    def execute(self, context):
        wm = context.window_manager
        prompt = wm.chiron_chat_prompt.strip()
        if not prompt:
            _set_chat_status(wm, "Enter a prompt")
            self.report({"WARNING"}, "Enter a prompt")
            return {"CANCELLED"}
        history = _load_chat_history(wm)
        payload = {"prompt": prompt, "history": history, "actions": list(_CHAT_ACTIONS)}
        if wm.chiron_chat_use_context:
            payload["context"] = _collect_blender_context()
        model = _normalize_model_name(wm.chiron_chat_model)
        if model:
            payload["model"] = model
        try:
            response = _http_post(f"{_server_url()}/chat", payload)
        except Exception as e:
            _set_chat_status(wm, "Chat request failed")
            self.report({"ERROR"}, f"Chat request failed: {e}")
            return {"CANCELLED"}
        if not response.get("ok"):
            error = response.get("error") or "Chat failed"
            if error == "llm_not_configured":
                message = "LLM not configured"
            elif error == "llm_failed":
                message = "LLM request failed"
            elif error == "missing_prompt":
                message = "Enter a prompt"
            else:
                message = error.replace("_", " ").strip() or "Chat failed"
            _set_chat_status(wm, message)
            self.report({"ERROR"}, message)
            return {"CANCELLED"}
        reply = str(response.get("reply", "")).strip()
        _append_chat_history(wm, "user", prompt)
        if reply:
            _append_chat_history(wm, "assistant", reply)
        _apply_chat_actions(wm, response.get("actions"))
        wm.chiron_chat_prompt = ""
        model_name = str(response.get("model", "")).strip()
        if model_name:
            _set_chat_status(wm, f"Reply received (model: {model_name})")
        else:
            _set_chat_status(wm, "Reply received")
        self.report({"INFO"}, "Reply received")
        return {"FINISHED"}


class CHIRON_OT_lesson_generate(bpy.types.Operator):
    bl_idname = "chiron.lesson_generate"
    bl_label = "Generate Lesson"
    bl_description = "Generate a lesson for the selected topic"

    def execute(self, context):
        wm = context.window_manager
        path_id = wm.chiron_active_learning_path
        topic_key = wm.chiron_active_topic
        if not path_id or path_id == "NONE":
            _set_topic_status(wm, "Select a learning path")
            self.report({"WARNING"}, "Select a learning path first")
            return {"CANCELLED"}
        if not topic_key or topic_key == "NONE":
            _set_topic_status(wm, "Select a topic")
            self.report({"WARNING"}, "Select a topic first")
            return {"CANCELLED"}
        if topic_key in lesson_tracking.get_completed_topics():
            _set_topic_status(wm, "Topic already completed")
            self.report({"WARNING"}, "Topic already completed")
            return {"CANCELLED"}
        path_id, slug = learning_paths.split_topic_key(topic_key)
        if not path_id or not slug:
            _set_topic_status(wm, "Invalid topic")
            self.report({"WARNING"}, "Invalid topic selection")
            return {"CANCELLED"}
        lesson_id = learning_paths.lesson_id_for_topic(topic_key)
        wm.chiron_current_topic_key = topic_key
        wm.chiron_lesson_id = lesson_id
        wm.chiron_step_index = 0
        wm.chiron_step_hint = ""
        _set_status(wm, "In progress")
        _set_topic_status(wm, f"Lesson loaded: {learning_paths.topic_label(slug)}")
        _save_progress(wm)
        self.report({"INFO"}, "Lesson generated")
        return {"FINISHED"}


class CHIRON_OT_lesson_history_reset(bpy.types.Operator):
    bl_idname = "chiron.lesson_history_reset"
    bl_label = "Reset Lesson History"
    bl_description = "Clear completed lesson topics"

    def execute(self, context):
        wm = context.window_manager
        lesson_tracking.reset_history()
        _set_topic_status(wm, "Lesson history cleared")
        self.report({"INFO"}, "Lesson history cleared")
        return {"FINISHED"}


class CHIRON_OT_lesson_start(bpy.types.Operator):
    bl_idname = "chiron.lesson_start"
    bl_label = "Start Lesson"
    bl_description = "Start or reset the current lesson"

    def execute(self, context):
        wm = context.window_manager
        wm.chiron_lesson_id = _get_lesson_id(wm)
        wm.chiron_step_index = 0
        wm.chiron_step_hint = ""
        if lesson_runtime.get_step(wm.chiron_lesson_id, wm.chiron_step_index):
            _set_status(wm, "In progress")
        else:
            _set_status(wm, "No steps")
        # Diagram UI disabled for now.
        # _update_diagram_for_current_step(wm)
        _save_progress(wm)
        self.report({"INFO"}, "Lesson started")
        return {"FINISHED"}


class CHIRON_OT_lesson_prev(bpy.types.Operator):
    bl_idname = "chiron.lesson_prev"
    bl_label = "Previous"
    bl_description = "Go to previous step"

    def execute(self, context):
        wm = context.window_manager
        if wm.chiron_step_index > 0:
            wm.chiron_step_index -= 1
            wm.chiron_step_hint = ""
            _set_status(wm, "In progress")
            # Diagram UI disabled for now.
            # _update_diagram_for_current_step(wm)
            _save_progress(wm)
        return {"FINISHED"}


class CHIRON_OT_lesson_next(bpy.types.Operator):
    bl_idname = "chiron.lesson_next"
    bl_label = "Next"
    bl_description = "Validate and advance to next step"

    def execute(self, context):
        wm = context.window_manager
        lesson_id = _get_lesson_id(wm)
        steps = lesson_runtime.get_lesson_steps(lesson_id)
        if not steps:
            _set_status(wm, "No steps")
            return {"CANCELLED"}
        current_index = wm.chiron_step_index
        if current_index >= len(steps):
            _set_status(wm, "Lesson complete")
            return {"FINISHED"}
        if not lesson_runtime.validate_step(lesson_id, current_index):
            _set_status(wm, "Step not complete")
            self.report({"WARNING"}, "Step not complete")
            return {"CANCELLED"}
        if current_index + 1 < len(steps):
            wm.chiron_step_index += 1
            wm.chiron_step_hint = ""
            _set_status(wm, "In progress")
            # Diagram UI disabled for now.
            # _update_diagram_for_current_step(wm)
            _save_progress(wm)
            return {"FINISHED"}
        _set_status(wm, "Lesson complete")
        if lesson_tracking.mark_topic_completed(wm.chiron_current_topic_key):
            _set_topic_status(wm, "Topic completed")
        _save_progress(wm)
        self.report({"INFO"}, "Lesson complete")
        return {"FINISHED"}


class CHIRON_OT_lesson_hint(bpy.types.Operator):
    bl_idname = "chiron.lesson_hint"
    bl_label = "Hint"
    bl_description = "Show a hint for the current step"

    def execute(self, context):
        wm = context.window_manager
        lesson_id = _get_lesson_id(wm)
        step = lesson_runtime.get_step(lesson_id, wm.chiron_step_index)
        if not step:
            _set_status(wm, "No step")
            return {"CANCELLED"}
        wm.chiron_step_hint = step.hint
        self.report({"INFO"}, step.hint)
        return {"FINISHED"}


class CHIRON_OT_lesson_show_me(bpy.types.Operator):
    bl_idname = "chiron.lesson_show_me"
    bl_label = "Show Me"
    bl_description = "Apply a safe, guided action for the current step"

    def execute(self, context):
        wm = context.window_manager
        lesson_id = _get_lesson_id(wm)
        ok = lesson_runtime.run_show_me(lesson_id, wm.chiron_step_index)
        if ok:
            _set_status(wm, "Show me applied")
            self.report({"INFO"}, "Show me applied")
            return {"FINISHED"}
        _set_status(wm, "No show me for this step")
        self.report({"WARNING"}, "No show me for this step")
        return {"CANCELLED"}
