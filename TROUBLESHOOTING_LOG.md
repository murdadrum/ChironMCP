# ChironMCP Troubleshooting Log (v0.1.1 -> v0.1.11)

This log summarizes add-on demo UI overlay troubleshooting and related changes from v0.1.1 through v0.1.11. It is intended to hand off to devs continuing investigation.

## Scope

- Blender add-on overlay demo (toast/highlight) not visible in Blender 5.0.
- MCP server connectivity OK; overlay drawing not visible despite operator responses.

## Timeline Summary

### v0.1.1
- Added demo inputs and operators in Blender panel (toast + highlight).
- Added WindowManager properties for message/target.

Code added (operators + UI):
```python
class CHIRON_OT_send_toast(bpy.types.Operator):
    bl_idname = "chiron.send_toast"
    def execute(self, context):
        payload = {"message": wm.chiron_toast_message, "level": "INFO"}
        response = _http_post("http://localhost:8000/blender/toast", payload)
        if response.get("ok"):
            self.report({"INFO"}, f"Toast sent: {response.get('message', '')}")
            return {"FINISHED"}
```

### v0.1.2
- Added draw handler overlay using `SpaceView3D.draw_handler_add(..., POST_PIXEL)`.
- Added toast banner and highlight border rendering.

Code added (draw handler):
```python
_DRAW_HANDLE = bpy.types.SpaceView3D.draw_handler_add(
    _draw_callback_px,
    (),
    "WINDOW",
    "POST_PIXEL",
)
```

### v0.1.3
- Added compatibility fallbacks for `blf.size` and `gpu.state` methods.
- Added more robust region lookup.

Code change (blf size fallback):
```python
try:
    blf.size(font_id, size, 72)
except TypeError:
    blf.size(font_id, size)
```

### v0.1.4
- Forced region to be `WINDOW` region for VIEW_3D.
- Still no visible overlay.

### v0.1.5
- Added debug overlay text: `CHIRON OVERLAY ACTIVE`.

Code added (debug overlay):
```python
if _DEBUG_OVERLAY:
    _draw_text("CHIRON OVERLAY ACTIVE", 20, 20, size=18)
```

### v0.1.6
- Adjusted region filtering to force `WINDOW` region.
- Overlay still not visible.

### v0.1.7
- Boosted visual contrast (bright red outline, green toast).
- Added debug text with region size.

Code added (debug region text):
```python
_draw_text(f"REGION {region.type} {w}x{h}", 20, 42, size=12)
```

### v0.1.8
- Added magenta full-screen tint on debug to confirm GPU drawing.
- Still invisible in Blender 5.0.

Code added (full-screen tint):
```python
_draw_rect_filled(0, 0, w, h, (0.6, 0.0, 0.6, 0.12))
```

### v0.1.9
- Added `bgl` fallback rendering and forced redraw timer.
- Blender 5.0 error: `No module named 'bgl'` on install.

Code added (bgl path):
```python
import bgl
bgl.glBegin(bgl.GL_QUADS)
# ...
bgl.glEnd()
```

### v0.1.10
- Made `bgl` import optional; only used if available.

Code change (optional bgl):
```python
try:
    import bgl
except Exception:
    bgl = None
```

### v0.1.11
- Made overlay handler persistent on add-on register.
- Overlay still not visible after clicking demo buttons.

Code change (register/unregister):
```python
def register():
    # ...
    operators.ensure_overlay_handler()

def unregister():
    # ...
    operators.remove_overlay_handler()
```

## Observed Behavior

- Server responses OK (toast/highlight responses in Blender info log).
- UI panel shows demo fields and buttons.
- Debug overlay text appeared in earlier versions (v0.1.7) but disappeared later on v0.1.10+.
- Blender 5.0 lacks `bgl` module (import error).

## Working Hypotheses

1) Draw handler is attached but running in an unexpected region or context.
2) GPU/POST_PIXEL draw in Blender 5.0 may need different hook or `POST_VIEW`.
3) Another overlay pipeline or context switch is preventing pixel overlay.
4) Region context lost after operator returns; explicit area/region binding may be required.

## Commands/Steps Used

Rebuild add-on zip:
```bash
scripts/build_addon_zip.sh
```

Server startup:
```bash
cd packages/chiron_mcp_server
uv run python -m chiron_mcp_server.server
```

## Next Debug Ideas

- Switch draw handler to `POST_VIEW` and test.
- Use `bpy.types.SpaceView3D.draw_handler_add` with an explicit region context by caching `context.area` and `context.region` from operator.
- Add a small permanent text overlay on register to verify draw callback execution.
- Log draw callback frequency and context to Blender console.
- Consider using `gpu_extras` + `gpu.matrix` with explicit viewport to avoid implicit region sizing.

## Files Touched (Core)

- `packages/chiron_blender_addon/chiron_mcp_addon/operators.py`
- `packages/chiron_blender_addon/chiron_mcp_addon/ui.py`
- `packages/chiron_blender_addon/chiron_mcp_addon/__init__.py`

