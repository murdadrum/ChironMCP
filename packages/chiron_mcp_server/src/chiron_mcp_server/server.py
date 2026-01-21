from __future__ import annotations

import base64
import io
from dataclasses import dataclass
from typing import Any, Dict, Optional

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:  # pragma: no cover
    Image = None
    ImageDraw = None
    ImageFont = None

mcp = FastMCP("ChironMCP Server", json_response=True)

# ---- In-memory session state (placeholder for future persistence) ----


@dataclass
class LessonState:
    lesson_id: Optional[str] = None
    step_index: int = 0


STATE = LessonState()

# ---- Tools ----


@mcp.tool()
def ping() -> str:
    """Sanity check: verify the MCP server is running."""
    return "pong"


@mcp.tool()
def lesson_start(lesson_id: str) -> Dict[str, Any]:
    """Start a lesson session."""
    STATE.lesson_id = lesson_id
    STATE.step_index = 0
    return {"ok": True, "lesson_id": STATE.lesson_id, "step_index": STATE.step_index}


@mcp.tool()
def lesson_next() -> Dict[str, Any]:
    """Advance to next step."""
    if STATE.lesson_id is None:
        return {"ok": False, "error": "No active lesson"}
    STATE.step_index += 1
    return {"ok": True, "lesson_id": STATE.lesson_id, "step_index": STATE.step_index}


@mcp.tool()
def lesson_get_state() -> Dict[str, Any]:
    """Get current lesson state."""
    return {"lesson_id": STATE.lesson_id, "step_index": STATE.step_index}


# These are tutorial primitives that Blender add-on can implement locally.
# For now they just echo, but later you can proxy calls to Blender.


@mcp.tool()
def ui_toast(message: str, level: str = "INFO") -> Dict[str, Any]:
    """Request Blender to show a toast (addon must implement)."""
    return {"ok": True, "message": message, "level": level}


@mcp.tool()
def ui_highlight(target: str) -> Dict[str, Any]:
    """Request Blender to highlight a UI target (addon must implement)."""
    return {"ok": True, "target": target}


# ---- Resources (placeholders until Blender context is wired) ----


@mcp.resource("chiron://status")
def status() -> str:
    """Server status resource."""
    return "ChironMCP server is running."


_FALLBACK_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/"
    "x8AAwMCAO+X9ZkAAAAASUVORK5CYII="
)


def _render_diagram_png(spec: Dict[str, Any]) -> bytes:
    if Image is None or ImageDraw is None:
        return base64.b64decode(_FALLBACK_PNG_BASE64)

    width = int(spec.get("width", 640))
    height = int(spec.get("height", 240))
    editor = str(spec.get("editor", ""))
    tab = str(spec.get("tab", ""))
    callout = str(spec.get("callout", ""))
    breadcrumbs = spec.get("breadcrumbs", [])

    img = Image.new("RGBA", (width, height), (36, 36, 36, 255))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    draw.rectangle([0, 0, width, 36], fill=(52, 52, 52, 255))
    draw.text((12, 10), f"{editor}  {tab}".strip(), font=font, fill=(230, 230, 230, 255))
    draw.rectangle([12, 60, width - 12, height - 12], outline=(180, 180, 180, 255), width=2)
    draw.text((20, 80), callout or "Follow the highlighted UI element.", font=font, fill=(240, 240, 240, 255))
    if breadcrumbs:
        crumb_text = " > ".join(str(item) for item in breadcrumbs)
        draw.text((20, 110), crumb_text, font=font, fill=(200, 200, 200, 255))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ---- HTTP endpoints for Blender add-on ----


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    return JSONResponse({"ok": True, "status": "ok", "name": mcp.name})


@mcp.custom_route("/blender/toast", methods=["POST"])
async def blender_toast(request: Request) -> JSONResponse:
    payload = await request.json()
    message = payload.get("message", "")
    level = payload.get("level", "INFO")
    return JSONResponse({"ok": True, "message": message, "level": level})


@mcp.custom_route("/blender/highlight", methods=["POST"])
async def blender_highlight(request: Request) -> JSONResponse:
    payload = await request.json()
    target = payload.get("target", "")
    return JSONResponse({"ok": True, "target": target})


@mcp.custom_route("/ui/diagram", methods=["POST"])
async def ui_diagram(request: Request) -> JSONResponse:
    payload = await request.json()
    png_bytes = _render_diagram_png(payload)
    b64 = base64.b64encode(png_bytes).decode("ascii")
    return JSONResponse({"ok": True, "image_base64": b64, "mime": "image/png"})


def create_app():
    return mcp.streamable_http_app()


if __name__ == "__main__":
    # Streamable HTTP is convenient for local dev and the MCP Inspector
    mcp.run(transport="streamable-http")
