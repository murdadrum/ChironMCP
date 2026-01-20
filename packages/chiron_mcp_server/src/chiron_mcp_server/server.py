from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

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


def create_app():
    return mcp.streamable_http_app()


if __name__ == "__main__":
    # Streamable HTTP is convenient for local dev and the MCP Inspector
    mcp.run(transport="streamable-http")
