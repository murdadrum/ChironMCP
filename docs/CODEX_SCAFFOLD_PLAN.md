SBelow is a **step-by-step scaffold plan** your Codex agent can execute end-to-end to initialize **ChironMCP** as a clean, product-ready foundation: **a GPL-friendly Blender add-on** + **a separate MCP server** (local now; later swappable to “Chiron Cloud Brain”).

I’m assuming the repo is currently empty at `murdadrum/ChironMCP`. (I couldn’t reliably open that repo in my web tool; GitHub search didn’t surface it, which usually means it’s new/empty or private.)

This plan deliberately aligns with Blender’s licensing expectations for Python add-ons (GPL-compatible distribution) and your “no subscription rent extraction” philosophy. ([Blender][1])
It also uses the official MCP spec and Python SDK approach. ([Model Context Protocol][2])

---

## Codex Task Breakdown: ChironMCP Scaffold (Repo Init → Running Demo)

### 0) Goals for v0 scaffold

- Repo builds cleanly on day 1
- Blender add-on is thin, GPL-friendly, safe-by-default
- MCP server exposes a minimal **tool surface** for:
  - reading scene context (safe)
  - tutorial primitives (highlight/toast + step state)

- No “arbitrary python execution” tool in production (dev-only pattern later)

---

# 1) Repo bootstrap

### 1.1 Clone and set up baseline

```bash
git clone https://github.com/murdadrum/ChironMCP.git
cd ChironMCP
```

### 1.2 Create baseline directories

```bash
mkdir -p docs
mkdir -p packages/chiron_mcp_server/src/chiron_mcp_server
mkdir -p packages/chiron_blender_addon/chiron_mcp_addon
mkdir -p .github/workflows
```

---

# 2) Write README with philosophy statement (public-facing)

Create `README.md`:

````md
# ChironMCP

**ChironMCP** is the MCP-enabled bridge that lets Blender host _guided, interactive learning experiences_ without compromising Blender’s open-source ethos.

## Philosophy

Blender’s ecosystem is built on openness. ChironMCP respects that:

- The Blender add-on is intentionally **thin, inspectable, and GPL-compatible**.
- Chiron’s value is not “locking down Blender.” It’s **teaching**, **verification**, and **curated learning design**.
- We avoid “rent extraction” subscription models. Users should feel like they **own what they buy**.

Blender’s licensing guidance is clear that Python add-ons using Blender’s API must be GPL-compatible when distributed, and that selling is limited to the download service (customers receive the same GPL freedoms). We embrace that.  
(See Blender license/FAQ.)

## What this repo contains

- `packages/chiron_blender_addon/`  
  A Blender add-on (GPL-friendly) that:
  - exposes a safe tool surface for tutoring
  - renders tutorial UI in Blender
  - reports context + validates step completion locally

- `packages/chiron_mcp_server/`  
  An MCP server that:
  - exposes Chiron tools/resources/prompts to MCP-compatible hosts
  - can run locally for development
  - can later proxy to a “Chiron Cloud Brain”

## Non-goals

- No “execute arbitrary Python” in production.
- No DRM theater. We gate value through **lesson packs, updates, and quality**—not hostility.

## Quickstart (dev)

### 1) Run MCP server

```bash
cd packages/chiron_mcp_server
uv sync
uv run python -m chiron_mcp_server.server
```
````

### 2) Install Blender add-on (dev)

In Blender:

- Edit → Preferences → Add-ons → Install…
- Select `packages/chiron_blender_addon/chiron_mcp_addon.zip` (build step below)
- Enable “ChironMCP”

### 3) Verify

- Open the sidebar panel (N-panel) → “Chiron”
- Click “Ping Server”
- Confirm you see a toast + a successful response

## Roadmap

- Tutorial runtime (local): UI highlights + deterministic step checks
- Signed lesson packs: versioned, cacheable, offline-friendly
- Auth gateway: OAuth device flow to a future Chiron Cloud Brain
- Multi-model support: Gemini today; pluggable model adapters tomorrow

## License

- Blender add-on: GPL-compatible (required by Blender’s licensing for distributed add-ons)
- MCP server: MIT (recommended) or GPL-compatible as needed, depending on linkage and distribution strategy

````

(When you publish, add the Blender license/FAQ citations as links; in this chat I’m citing the underlying sources. :contentReference[oaicite:2]{index=2})

---

# 3) Add top-level docs

### 3.1 Add `docs/ARCHITECTURE.md`
```md
# Architecture

## Principle
Blender add-on = thin “gateway” (GPL-friendly)
Chiron Brain = swappable (local now, cloud later)

## Components

### Blender Add-on
- UI panel for lesson steps
- Local tutorial runtime + step validation
- Safe execution surface (allowlisted operators only)
- Context snapshot emitter

### MCP Server
- Implements MCP over Streamable HTTP (dev-friendly)
- Exposes:
  - Resources: scene summary, selection summary
  - Tools: ping, highlight, toast, lesson state, step check
  - Prompts: structured lesson templates

## Why MCP
MCP standardizes tools/resources/prompts over JSON-RPC transports, enabling interoperability across host apps and models.
See MCP specification and official Python SDK docs.
````

(MCP spec + SDK refs: ([Model Context Protocol][2]))

---

# 4) Scaffold MCP server package (Python + uv + FastMCP)

We’ll use the official MCP Python SDK path (`mcp[cli]`) which includes a `FastMCP` developer experience. ([GitHub][3])
(Their repo notes v2 is pre-alpha and v1.x is recommended for production; for now we’ll pin stable v1.x by using a caret constraint. ([GitHub][3]))

### 4.1 Create `packages/chiron_mcp_server/pyproject.toml`

```toml
[project]
name = "chiron-mcp-server"
version = "0.1.0"
description = "Chiron MCP server for Blender tutoring tools"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
  "mcp[cli]>=1.0.0,<2.0.0",
]

[project.optional-dependencies]
dev = [
  "ruff>=0.5.0",
  "pytest>=8.0.0",
]

[tool.ruff]
line-length = 100
target-version = "py311"
```

### 4.2 Create `packages/chiron_mcp_server/README.md`

````md
# chiron-mcp-server

Local MCP server for ChironMCP development.

Run:

```bash
uv sync --group dev
uv run python -m chiron_mcp_server.server
```
````

````

### 4.3 Add `packages/chiron_mcp_server/src/chiron_mcp_server/server.py`
```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from mcp.server.fastmcp import FastMCP

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

if __name__ == "__main__":
    # Streamable HTTP is convenient for local dev and the MCP Inspector
    mcp.run(transport="streamable-http")
````

### 4.4 Add `packages/chiron_mcp_server/src/chiron_mcp_server/__init__.py`

```python
__all__ = ["__version__"]
__version__ = "0.1.0"
```

### 4.5 Add `packages/chiron_mcp_server/uv.lock` via:

```bash
cd packages/chiron_mcp_server
uv sync --group dev
cd ../..
```

---

# 5) Scaffold Blender add-on (thin gateway + UI panel)

### 5.1 Add add-on metadata: `packages/chiron_blender_addon/chiron_mcp_addon/__init__.py`

```python
bl_info = {
    "name": "ChironMCP",
    "author": "murdadrum",
    "version": (0, 1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Chiron",
    "description": "Thin GPL-friendly gateway addon for Chiron tutorial UI + MCP bridge.",
    "category": "3D View",
}

import bpy
from . import operators, ui

classes = (
    operators.CHIRON_OT_ping_server,
    ui.CHIRON_PT_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
```

### 5.2 Add operator: `packages/chiron_blender_addon/chiron_mcp_addon/operators.py`

```python
import bpy
import urllib.request
import json

DEFAULT_MCP_HTTP = "http://localhost:8000/mcp"

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

class CHIRON_OT_ping_server(bpy.types.Operator):
    bl_idname = "chiron.ping_server"
    bl_label = "Ping Server"
    bl_description = "Ping the local Chiron MCP server"

    def execute(self, context):
        try:
            # Minimal JSON-RPC call expected by MCP transport endpoints will vary;
            # this is a placeholder. We'll switch to the MCP client later.
            # For now just hit the resource endpoint if you add one,
            # or use a dedicated /health endpoint in dev.
            self.report({"INFO"}, "Ping placeholder - wire MCP client next")
            return {"FINISHED"}
        except Exception as e:
            self.report({"ERROR"}, f"Ping failed: {e}")
            return {"CANCELLED"}
```

**Note:** The MCP server’s Streamable HTTP endpoint speaks MCP protocol—not plain JSON-RPC you should hand-roll. In the next step we’ll add an MCP client (or a tiny proxy endpoint) for the Blender addon. This scaffold keeps Blender-side dependencies minimal and safe.

### 5.3 Add panel UI: `packages/chiron_blender_addon/chiron_mcp_addon/ui.py`

```python
import bpy

class CHIRON_PT_panel(bpy.types.Panel):
    bl_label = "Chiron"
    bl_idname = "CHIRON_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Chiron"

    def draw(self, context):
        layout = self.layout
        layout.label(text="ChironMCP (dev scaffold)")
        layout.operator("chiron.ping_server", icon="URL")
```

---

# 6) Add packaging script for Blender add-on zip

Create `scripts/build_addon_zip.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ADDON_DIR="$ROOT/packages/chiron_blender_addon/chiron_mcp_addon"
OUT_DIR="$ROOT/dist"
mkdir -p "$OUT_DIR"

ZIP_PATH="$OUT_DIR/chiron_mcp_addon.zip"
rm -f "$ZIP_PATH"

(
  cd "$ADDON_DIR/.."
  zip -r "$ZIP_PATH" "chiron_mcp_addon" -x "*.DS_Store"
)

echo "Built: $ZIP_PATH"
```

Make executable:

```bash
chmod +x scripts/build_addon_zip.sh
```

---

# 7) Lint + tests + CI

### 7.1 Add root `.editorconfig`

```ini
root = true

[*]
end_of_line = lf
insert_final_newline = true
charset = utf-8

[*.py]
indent_style = space
indent_size = 4
```

### 7.2 Add `packages/chiron_mcp_server/tests/test_smoke.py`

```python
def test_smoke():
    assert True
```

### 7.3 Add GitHub Actions: `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
  pull_request:

jobs:
  python:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: packages/chiron_mcp_server
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync --group dev
      - run: uv run ruff check .
      - run: uv run pytest -q
```

---

# 8) Commit + tag v0 scaffold

```bash
git add -A
git commit -m "Scaffold ChironMCP: MCP server + Blender addon + docs + CI"
git push origin main
```

---

# 9) Next sprint (immediately after scaffold): make it actually interactive

These are the first “real product” tasks Codex should implement next:

### 9.1 Add an MCP client layer (don’t hand-roll protocol)

- Option A: add Python MCP client inside Blender add-on (harder; Blender Python env constraints)
- Option B (recommended): add a tiny local bridge endpoint in the server:
  - `/health`
  - `/blender/toast`
  - `/blender/highlight`
    …and keep the Blender add-on speaking simple HTTP to the local server.

### 9.2 Implement tutorial primitives locally in Blender

- `ui_highlight(target)` → draw handler overlay + UI cues
- `ui_toast(message)` → `self.report` + panel message area
- `step_check(step_id)` → deterministic scene checks (no LLM guessing)

### 9.3 Lesson packs (declarative + cacheable)

Create:

- `lesson_packs/core_basics_v1.json`
- local cache folder
- simple signature stub (later real signing)

---

## README Philosophy statement: sourcing notes for public release

When you publish and want to cite sources, Blender’s own site explicitly describes:

- Blender respects privacy and doesn’t require internet by default
- Python add-ons using Blender’s Python API must be GPL-compatible when distributed
- Selling is allowed but “restricted to the download service itself,” and customers receive the same GPL freedoms ([Blender][1])

For MCP references:

- Official specification page ([Model Context Protocol][2])
- Official Python SDK + FastMCP quickstart guidance ([GitHub][3])

---

If you want, I can also generate a **single “Codex execution script”** (a linear list of file writes + commands) that your agent can follow without any interpretation—basically a reproducible scaffold recipe.

[1]: https://www.blender.org/about/license/?utm_source=chatgpt.com "License — Blender"
[2]: https://modelcontextprotocol.io/specification/2024-11-05?utm_source=chatgpt.com "Specification - Model Context Protocol"
[3]: https://github.com/modelcontextprotocol/python-sdk?utm_source=chatgpt.com "GitHub - modelcontextprotocol/python-sdk: The official Python SDK for Model Context Protocol servers and clients"
