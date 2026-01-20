````bash
#!/usr/bin/env bash
set -euo pipefail

# ChironMCP repo scaffold script
# Usage:
#   1) git clone https://github.com/murdadrum/ChironMCP.git
#   2) cd ChironMCP
#   3) bash ./codex_scaffold.sh
#
# Notes:
# - This script scaffolds:
#   - docs/
#   - packages/chiron_mcp_server (Python + uv + MCP FastMCP)
#   - packages/chiron_blender_addon (Blender addon skeleton)
#   - CI workflow
#   - build script for addon zip
# - It does NOT implement full MCP client calls from Blender yet (intentional).
#   The addon is a thin UI gateway. Next sprint will wire real transport.

ROOT="$(pwd)"

echo "==> Verifying we're in a git repo..."
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
  echo "ERROR: Not inside a git repo. Run this from the ChironMCP repo root."
  exit 1
}

echo "==> Creating directories..."
mkdir -p docs
mkdir -p packages/chiron_mcp_server/src/chiron_mcp_server
mkdir -p packages/chiron_mcp_server/tests
mkdir -p packages/chiron_blender_addon/chiron_mcp_addon
mkdir -p .github/workflows
mkdir -p scripts
mkdir -p dist

echo "==> Writing README.md..."
cat > README.md <<'EOF'
# ChironMCP

**ChironMCP** is the MCP-enabled bridge that lets Blender host *guided, interactive learning experiences* without compromising Blender’s open-source ethos.

## Philosophy

Blender’s ecosystem is built on openness. ChironMCP respects that:

- The Blender add-on is intentionally **thin, inspectable, and GPL-compatible**.
- Chiron’s value is not “locking down Blender.” It’s **teaching**, **verification**, and **curated learning design**.
- We avoid “rent extraction” subscription models. Users should feel like they **own what they buy**.

Blender’s licensing guidance is clear that Python add-ons using Blender’s API must be GPL-compatible when distributed, and that selling is limited to the download service (customers receive the same GPL freedoms). We embrace that.

## What this repo contains

- `packages/chiron_blender_addon/`
  A Blender add-on (GPL-friendly) that:
  - exposes a safe tool surface for tutoring
  - renders tutorial UI in Blender
  - reports context + validates step completion locally (future sprint)

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
uv sync --group dev
uv run python -m chiron_mcp_server.server
````

### 2) Build and install Blender add-on (dev)

```bash
./scripts/build_addon_zip.sh
```

In Blender:

- Edit → Preferences → Add-ons → Install…
- Select `dist/chiron_mcp_addon.zip`
- Enable “ChironMCP”

### 3) Verify

- Open the sidebar panel (N-panel) → “Chiron”
- Click “Ping Server” (placeholder until MCP client wiring)

## Roadmap

- Tutorial runtime (local): UI highlights + deterministic step checks
- Signed lesson packs: versioned, cacheable, offline-friendly
- Auth gateway: OAuth device flow to a future Chiron Cloud Brain
- Multi-model support: Gemini today; pluggable model adapters tomorrow

## License

- Blender add-on: GPL-compatible (recommended/expected for Blender Python add-ons using Blender API)
- MCP server: MIT (recommended) or GPL-compatible as needed, depending on distribution strategy
  EOF

echo "==> Writing docs/ARCHITECTURE.md..."
cat > docs/ARCHITECTURE.md <<'EOF'

# Architecture

## Principle

Blender add-on = thin “gateway” (GPL-friendly)
Chiron Brain = swappable (local now, cloud later)

## Components

### Blender Add-on

- UI panel for lesson steps (scaffold now)
- Local tutorial runtime + step validation (next sprint)
- Safe execution surface (allowlisted operators only; no raw code exec)
- Context snapshot emitter (next sprint)

### MCP Server

- Implements MCP via FastMCP (streamable HTTP for dev)
- Exposes:
  - Resources: basic server status
  - Tools: ping, lesson state, tutorial primitives placeholders

## Why MCP

MCP standardizes tools/resources/prompts over supported transports, enabling interoperability across host apps and models.
EOF

echo "==> Writing .editorconfig..."
cat > .editorconfig <<'EOF'
root = true

[*]
end_of_line = lf
insert_final_newline = true
charset = utf-8

[*.py]
indent_style = space
indent_size = 4
EOF

echo "==> Writing MCP server package files..."
cat > packages/chiron_mcp_server/README.md <<'EOF'

# chiron-mcp-server

Local MCP server for ChironMCP development.

Run:

```bash
uv sync --group dev
uv run python -m chiron_mcp_server.server
```

EOF

cat > packages/chiron_mcp_server/pyproject.toml <<'EOF'
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
EOF

cat > packages/chiron_mcp_server/src/chiron_mcp_server/**init**.py <<'EOF'
**all** = ["**version**"]
**version** = "0.1.0"
EOF

cat > packages/chiron_mcp_server/src/chiron_mcp_server/server.py <<'EOF'
from **future** import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from mcp.server.fastmcp import FastMCP

# json_response=True makes the streamable-http transport respond with JSON

mcp = FastMCP("ChironMCP Server", json_response=True)

@dataclass
class LessonState:
lesson_id: Optional[str] = None
step_index: int = 0

STATE = LessonState()

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

# Tutorial primitives (placeholders until Blender-side wiring is added)

@mcp.tool()
def ui_toast(message: str, level: str = "INFO") -> Dict[str, Any]:
"""Request Blender to show a toast (addon must implement)."""
return {"ok": True, "message": message, "level": level}

@mcp.tool()
def ui_highlight(target: str) -> Dict[str, Any]:
"""Request Blender to highlight a UI target (addon must implement)."""
return {"ok": True, "target": target}

@mcp.resource("chiron://status")
def status() -> str:
"""Server status resource."""
return "ChironMCP server is running."

def main() -> None:

# Streamable HTTP is convenient for local dev and the MCP Inspector

mcp.run(transport="streamable-http")

if **name** == "**main**":
main()
EOF

cat > packages/chiron_mcp_server/tests/test_smoke.py <<'EOF'
def test_smoke():
assert True
EOF

echo "==> Writing Blender addon files..."
cat > packages/chiron_blender_addon/chiron_mcp_addon/**init**.py <<'EOF'
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
EOF

cat > packages/chiron_blender_addon/chiron_mcp_addon/operators.py <<'EOF'
import bpy

class CHIRON_OT_ping_server(bpy.types.Operator):
bl_idname = "chiron.ping_server"
bl_label = "Ping Server"
bl_description = "Ping the local Chiron MCP server (placeholder until MCP client wiring)"

```
def execute(self, context):
    # NOTE: Streamable HTTP MCP endpoints speak MCP protocol.
    # Next sprint: add a tiny local proxy endpoint in the server
    # (e.g., /health) OR embed an MCP client.
    self.report({"INFO"}, "Ping placeholder. Next: wire MCP client or /health proxy.")
    return {"FINISHED"}
```

EOF

cat > packages/chiron_blender_addon/chiron_mcp_addon/ui.py <<'EOF'
import bpy

class CHIRON_PT_panel(bpy.types.Panel):
bl_label = "Chiron"
bl_idname = "CHIRON_PT_panel"
bl_space_type = "VIEW_3D"
bl_region_type = "UI"
bl_category = "Chiron"

```
def draw(self, context):
    layout = self.layout
    layout.label(text="ChironMCP (dev scaffold)")
    layout.operator("chiron.ping_server", icon="URL")
```

EOF

echo "==> Writing addon build script..."
cat > scripts/build_addon_zip.sh <<'EOF'
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
zip -r "$ZIP_PATH" "chiron_mcp_addon" -x "\*.DS_Store"
)

echo "Built: $ZIP_PATH"
EOF
chmod +x scripts/build_addon_zip.sh

echo "==> Writing GitHub Actions workflow..."
cat > .github/workflows/ci.yml <<'EOF'
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
  EOF

echo "==> Initializing uv env for MCP server (if uv is installed)..."
if command -v uv >/dev/null 2>&1; then
(
cd packages/chiron_mcp_server
uv sync --group dev
)
else
echo "WARN: uv not found. Skipping uv sync. Install uv to run the server + CI locally."
fi

echo "==> Building Blender addon zip (if zip is installed)..."
if command -v zip >/dev/null 2>&1; then
./scripts/build_addon_zip.sh
else
echo "WARN: zip not found. Skipping addon zip build."
fi

echo "==> Git status:"
git status --porcelain

echo
echo "==> Done."
echo "Next:"
echo " 1) Run server: (cd packages/chiron_mcp_server && uv run python -m chiron_mcp_server.server)"
echo " 2) Install addon: dist/chiron_mcp_addon.zip in Blender Preferences > Add-ons"
echo " 3) Next sprint: wire real MCP client calls or add /health proxy endpoint."

```
::contentReference[oaicite:0]{index=0}
```
