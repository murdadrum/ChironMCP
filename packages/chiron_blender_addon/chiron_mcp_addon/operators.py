import json
import time
import urllib.request

import bpy
import blf
import gpu
from gpu_extras.batch import batch_for_shader

try:
    import bgl  # Blender < 4.x
except Exception:
    bgl = None

DEFAULT_MCP_HTTP = "http://localhost:8000"
_DRAW_HANDLE = None
_DRAW_AREA = None
_DRAW_REGION = None
_TOAST_MESSAGE = ""
_TOAST_EXPIRES = 0.0
_HIGHLIGHT_TARGET = ""
_HIGHLIGHT_EXPIRES = 0.0
_OVERLAY_TICK = 0.1
_TIMER_ACTIVE = False
_DEBUG_OVERLAY = False
_DEBUG_EXPIRES = 0.0


def _now() -> float:
    return time.time()


def _tag_redraw():
    wm = bpy.context.window_manager
    for window in wm.windows:
        for area in window.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()


def _ensure_draw_handler():
    global _DRAW_HANDLE
    if _DRAW_HANDLE is None:
        _DRAW_HANDLE = bpy.types.SpaceView3D.draw_handler_add(
            _draw_callback_px,
            (),
            "WINDOW",
            "POST_PIXEL",
        )


def _remove_draw_handler():
    global _DRAW_HANDLE
    if _DRAW_HANDLE is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_DRAW_HANDLE, "WINDOW")
        _DRAW_HANDLE = None


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


def _set_draw_context(context):
    global _DRAW_AREA, _DRAW_REGION
    try:
        if context.area and context.area.type == "VIEW_3D":
            _DRAW_AREA = context.area
        if context.region and context.region.type == "WINDOW":
            _DRAW_REGION = context.region
    except Exception:
        return


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

    if _DRAW_REGION is not None:
        region = _DRAW_REGION
    if _DRAW_AREA is not None:
        area = _DRAW_AREA

    if region is not None and region.type != "WINDOW":
        region = None

    if region is None and area and area.type == "VIEW_3D":
        for candidate in area.regions:
            if candidate.type == "WINDOW":
                region = candidate
                break

    if region is None:
        return

    w = region.width
    h = region.height

    if _TOAST_MESSAGE:
        padding = 10
        box_w = min(520, w - 2 * padding)
        box_h = 30
        x = padding
        y = h - box_h - padding
        _draw_rect_filled(x, y, box_w, box_h, (0.1, 0.5, 0.1, 0.9))
        _draw_text(_TOAST_MESSAGE, x + 8, y + 8, size=14, color=(1, 1, 1, 1))

    if _HIGHLIGHT_TARGET:
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
    with urllib.request.urlopen(req, timeout=2) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _http_get(url: str) -> dict:
    req = urllib.request.Request(
        url=url,
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=2) as resp:
        return json.loads(resp.read().decode("utf-8"))


class CHIRON_OT_ping_server(bpy.types.Operator):
    bl_idname = "chiron.ping_server"
    bl_label = "Ping Server"
    bl_description = "Ping the local Chiron MCP server"

    def execute(self, context):
        wm = context.window_manager
        try:
            response = _http_get(f"{DEFAULT_MCP_HTTP}/health")
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
            _set_draw_context(context)
            payload = {"message": wm.chiron_toast_message, "level": "INFO"}
            response = _http_post(f"{DEFAULT_MCP_HTTP}/blender/toast", payload)
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
            _set_draw_context(context)
            payload = {"target": wm.chiron_highlight_target}
            response = _http_post(f"{DEFAULT_MCP_HTTP}/blender/highlight", payload)
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
