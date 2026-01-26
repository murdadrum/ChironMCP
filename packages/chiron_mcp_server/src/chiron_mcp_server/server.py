from __future__ import annotations

import base64
import io
import json
import os
import urllib.request
import urllib.error
import socket
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any, Dict, Optional

from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from starlette.requests import Request
from starlette.responses import JSONResponse

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:  # pragma: no cover
    Image = None
    ImageDraw = None
    ImageFont = None

mcp = FastMCP("ChironMCP Server", json_response=True)

load_dotenv()

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


class _HeadingParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title: str = ""
        self.headings: list[str] = []
        self._buffer: list[str] = []
        self._in_heading: Optional[str] = None
        self._in_title = False

    def handle_starttag(self, tag: str, attrs):
        if tag in ("h1", "h2", "h3"):
            self._in_heading = tag
            self._buffer = []
        elif tag == "title":
            self._in_title = True
            self._buffer = []

    def handle_data(self, data: str):
        if self._in_heading or self._in_title:
            self._buffer.append(data)

    def handle_endtag(self, tag: str):
        if tag == "title" and self._in_title:
            text = "".join(self._buffer).strip()
            if text:
                self.title = text
            self._buffer = []
            self._in_title = False
        if tag in ("h1", "h2", "h3") and self._in_heading == tag:
            text = "".join(self._buffer).strip()
            if text:
                self.headings.append(text)
            self._buffer = []
            self._in_heading = None


def _fetch_html(url: str) -> str:
    timeout = float(os.environ.get("CHIRON_SOURCE_TIMEOUT", "20"))
    user_agent = os.environ.get(
        "CHIRON_SOURCE_USER_AGENT",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36",
    )
    cookie = os.environ.get("CHIRON_SOURCE_COOKIE", "").strip()
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    if cookie:
        req.add_header("Cookie", cookie)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        content_type = resp.headers.get("content-type", "")
        charset = "utf-8"
        if "charset=" in content_type:
            charset = content_type.split("charset=")[-1].split(";")[0].strip() or "utf-8"
        raw = resp.read(2_000_000)
    return raw.decode(charset, errors="ignore")


def _steps_from_html(html: str, url: str) -> Dict[str, Any]:
    parser = _HeadingParser()
    parser.feed(html)
    title = parser.title or "Tutorial Source"
    seen = set()
    headings = []
    for heading in parser.headings:
        if heading in seen:
            continue
        seen.add(heading)
        headings.append(heading)
        if len(headings) >= 6:
            break
    steps = [
        {
            "step_id": "open-source",
            "title": "Open the source",
            "instruction": f"Open the tutorial source: {url}",
            "hint": "Use your browser to read the material.",
        }
    ]
    for idx, heading in enumerate(headings, start=1):
        steps.append(
            {
                "step_id": f"section-{idx}",
                "title": f"Review: {heading}",
                "instruction": f"Review the section titled \"{heading}\".",
                "hint": "Note the key ideas and any steps you should try in Blender.",
            }
        )
    return {"title": title, "steps": steps}


def _llm_config() -> Optional[Dict[str, str]]:
    endpoint = os.environ.get("CHIRON_LLM_ENDPOINT", "").strip()
    api_key = os.environ.get("CHIRON_LLM_API_KEY", "").strip()
    model = os.environ.get("CHIRON_LLM_MODEL", "").strip() or "gpt-5.2"
    if model == "chatgpt-5.2":
        model = "gpt-5.2"
    if not endpoint or not api_key:
        return None
    return {"endpoint": endpoint, "api_key": api_key, "model": model}


def _llm_request(prompt: str, model: str, endpoint: str, api_key: str) -> str:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are Chiron. Return only JSON."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        body = resp.read().decode("utf-8", errors="ignore")
    return body


def _llm_chat_request(messages: list[dict], model: str, endpoint: str, api_key: str) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.3,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        body = resp.read().decode("utf-8", errors="ignore")
    return body


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    text = text.strip()
    if not text:
        return None
    candidate = text
    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        candidate = text[start : end + 1]
    try:
        payload = json.loads(candidate)
    except Exception:
        return None
    if isinstance(payload, dict):
        return payload
    return None


def _parse_llm_response(body: str) -> Optional[Dict[str, Any]]:
    payload = _extract_json(body)
    if not payload:
        return None
    if "choices" in payload and isinstance(payload.get("choices"), list):
        choice = payload["choices"][0] if payload["choices"] else {}
        message = choice.get("message") if isinstance(choice, dict) else {}
        content = ""
        if isinstance(message, dict):
            content = str(message.get("content", "")).strip()
        if not content and isinstance(choice, dict):
            content = str(choice.get("text", "")).strip()
        if content:
            return _extract_json(content)
        return None
    return payload


def _parse_llm_text_response(body: str) -> str:
    text = body.strip()
    if not text:
        return ""
    try:
        payload = json.loads(text)
    except Exception:
        return text
    if isinstance(payload, dict):
        if "choices" in payload and isinstance(payload.get("choices"), list):
            choice = payload["choices"][0] if payload["choices"] else {}
            if isinstance(choice, dict):
                message = choice.get("message")
                if isinstance(message, dict):
                    content = str(message.get("content", "")).strip()
                    if content:
                        return content
                text_reply = str(choice.get("text", "")).strip()
                if text_reply:
                    return text_reply
        for key in ("reply", "message", "content"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return text


def _coerce_llm_lesson(payload: Dict[str, Any], fallback_title: str) -> Optional[Dict[str, Any]]:
    title = str(payload.get("title", "")).strip() or fallback_title
    steps_in = payload.get("steps", [])
    if not isinstance(steps_in, list) or not steps_in:
        return None
    steps = []
    for idx, item in enumerate(steps_in, start=1):
        if not isinstance(item, dict):
            continue
        step_id = str(item.get("step_id", f"step-{idx}"))
        title_step = str(item.get("title", f"Step {idx}"))
        instruction = str(item.get("instruction", "")).strip()
        hint = str(item.get("hint", "")).strip()
        if not instruction:
            continue
        steps.append(
            {
                "step_id": step_id,
                "title": title_step,
                "instruction": instruction,
                "hint": hint,
            }
        )
    if not steps:
        return None
    return {"title": title, "steps": steps}


def _llm_lesson_from_html(html: str, url: str) -> Optional[Dict[str, Any]]:
    config = _llm_config()
    if not config:
        return None
    parser = _HeadingParser()
    parser.feed(html)
    title = parser.title or "Tutorial Source"
    headings = []
    seen = set()
    for heading in parser.headings:
        heading = heading.strip()
        if not heading or heading in seen:
            continue
        seen.add(heading)
        headings.append(heading)
        if len(headings) >= 10:
            break
    heading_text = "\n".join(f"- {item}" for item in headings) or "- (none)"
    prompt = (
        "Create a step-by-step Blender tutorial from this source.\n"
        "Return JSON with: title (string), steps (array of {step_id,title,instruction,hint}).\n"
        "Keep it to 4-8 steps. Use short, action-oriented instructions.\n"
        f"Source URL: {url}\n"
        f"Source Title: {title}\n"
        f"Headings:\n{heading_text}\n"
    )
    try:
        response = _llm_request(prompt, config["model"], config["endpoint"], config["api_key"])
    except Exception:
        return None
    payload = _parse_llm_response(response)
    if not payload:
        return None
    return _coerce_llm_lesson(payload, title)


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


@mcp.custom_route("/chat", methods=["POST"])
async def chat(request: Request) -> JSONResponse:
    payload = await request.json()
    prompt = str(payload.get("prompt", "")).strip()
    history = payload.get("history", [])
    context = payload.get("context")
    actions = payload.get("actions", [])
    model_override = str(payload.get("model", "")).strip()
    if not prompt:
        return JSONResponse({"ok": False, "error": "missing_prompt"}, status_code=400)
    config = _llm_config()
    if not config:
        return JSONResponse({"ok": False, "error": "llm_not_configured"}, status_code=503)
    model = model_override or config["model"]
    messages = [
        {
            "role": "system",
            "content": (
                "You are Chiron, a concise Blender assistant. Reply in plain text, "
                "or JSON with keys: reply (string) and optional actions (array)."
            ),
        }
    ]
    if context:
        messages.append(
            {
                "role": "system",
                "content": f"Blender context (JSON): {json.dumps(context)}",
            }
        )
    if actions:
        messages.append(
            {
                "role": "system",
                "content": (
                    "Allowed actions: "
                    + ", ".join(str(item) for item in actions if isinstance(item, str))
                ),
            }
        )
    if isinstance(history, list):
        for item in history:
            if not isinstance(item, dict):
                continue
            role = str(item.get("role", "")).strip()
            content = str(item.get("content", "")).strip()
            if role in ("user", "assistant", "system") and content:
                messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": prompt})
    try:
        response = _llm_chat_request(messages, model, config["endpoint"], config["api_key"])
    except Exception:
        return JSONResponse({"ok": False, "error": "llm_failed"}, status_code=502)
    text_reply = _parse_llm_text_response(response)
    if not text_reply:
        return JSONResponse({"ok": False, "error": "empty_response"}, status_code=502)
    parsed = _extract_json(text_reply)
    if isinstance(parsed, dict):
        reply = str(parsed.get("reply", "")).strip()
        actions_out = parsed.get("actions", [])
        if not reply:
            reply = text_reply
        return JSONResponse(
            {"ok": True, "reply": reply, "actions": actions_out, "model": model}
        )
    return JSONResponse({"ok": True, "reply": text_reply, "model": model})


@mcp.custom_route("/tutorial/source", methods=["POST"])
async def tutorial_source(request: Request) -> JSONResponse:
    payload = await request.json()
    url = str(payload.get("url", "")).strip()
    use_llm = bool(payload.get("use_llm", True))
    if not url or not (url.startswith("http://") or url.startswith("https://")):
        return JSONResponse({"ok": False, "error": "invalid_url"}, status_code=400)
    try:
        html = _fetch_html(url)
    except urllib.error.HTTPError as exc:
        return JSONResponse(
            {"ok": False, "error": "fetch_failed", "status": exc.code},
            status_code=502,
        )
    except (socket.timeout, TimeoutError):
        return JSONResponse(
            {"ok": False, "error": "fetch_timeout", "status": "timeout"},
            status_code=504,
        )
    except urllib.error.URLError as exc:
        if isinstance(getattr(exc, "reason", None), socket.timeout):
            return JSONResponse(
                {"ok": False, "error": "fetch_timeout", "status": "timeout"},
                status_code=504,
            )
        return JSONResponse({"ok": False, "error": "fetch_failed"}, status_code=502)
    except Exception:
        return JSONResponse({"ok": False, "error": "fetch_failed"}, status_code=502)
    llm_used = False
    llm_error: Optional[str] = None
    llm_lesson = None
    if use_llm:
        if _llm_config():
            llm_lesson = _llm_lesson_from_html(html, url)
            if llm_lesson:
                llm_used = True
            else:
                llm_error = "llm_failed"
        else:
            llm_error = "llm_not_configured"
    if llm_used and llm_lesson:
        return JSONResponse(
            {
                "ok": True,
                "lesson": llm_lesson,
                "source_url": url,
                "llm_used": True,
            }
        )
    lesson = _steps_from_html(html, url)
    return JSONResponse(
        {
            "ok": True,
            "lesson": lesson,
            "source_url": url,
            "llm_used": False,
            "llm_error": llm_error,
        }
    )


def create_app():
    return mcp.streamable_http_app()


if __name__ == "__main__":
    # Streamable HTTP is convenient for local dev and the MCP Inspector
    mcp.run(transport="streamable-http")
