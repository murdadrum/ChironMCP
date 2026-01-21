# ChironMCP

**ChironMCP** is the MCP-enabled bridge that lets Blender host _guided, interactive learning experiences_ without compromising Blender's open-source ethos.

## Philosophy

Blender's ecosystem is built on openness. ChironMCP respects that:

- The Blender add-on is intentionally **thin, inspectable, and GPL-compatible**.
- Chiron's value is not "locking down Blender." It's **teaching**, **verification**, and **curated learning design**.
- We avoid "rent extraction" subscription models. Users should feel like they **own what they buy**.

Blender's licensing guidance is clear that Python add-ons using Blender's API must be GPL-compatible when distributed, and that selling is limited to the download service (customers receive the same GPL freedoms). We embrace that.
(See Blender license/FAQ.)

## What this repo contains

- `packages/chiron_blender_addon/`
  A Blender add-on (GPL-friendly) that:
  - exposes a safe tool surface for tutoring
  - renders tutorial UI in Blender
  - reports context + validates step completion locally
  - supports Learning Paths with topic tracking

- `packages/chiron_mcp_server/`
  An MCP server that:
  - exposes Chiron tools/resources/prompts to MCP-compatible hosts
  - can run locally for development
  - can later proxy to a "Chiron Cloud Brain"

## Non-goals

- No "execute arbitrary Python" in production.
- No DRM theater. We gate value through **lesson packs, updates, and quality** -- not hostility.

## Quickstart (dev)

### 1) Run MCP server

```bash
cd packages/chiron_mcp_server
uv sync --group dev
uv run python -m chiron_mcp_server.server
```

### 2) Install Blender add-on (dev)

In Blender:

- Edit -> Preferences -> Add-ons -> Install...
- Select `packages/chiron_blender_addon/chiron_mcp_addon.zip` (build step below)
- Enable "ChironMCP"

If you update the add-on code and don't see changes:

- Rebuild the zip with `scripts/build_addon_zip.sh`
- Disable or remove the existing "ChironMCP" add-on in Preferences
- Restart Blender
- Install `dist/chiron_mcp_addon.zip` and enable it again

### 3) Verify

- Open the sidebar panel (N-panel) -> "Chiron"
- Click "Ping Server"
- Confirm you see a toast + a successful response
- Choose a Learning Path + topic and click "Generate Lesson"

## Learning Paths (demo)

Chiron mirrors the Blender manual structure to drive topic-based lessons.

- Enable "Modeling > Geometry Nodes" in Add-on Preferences.
- In the Chiron panel, pick a topic and click "Generate Lesson."
- Completed topics are hidden; use "Reset Lesson History" to re-test.
- Progress persists to `chiron/progress.json` and `chiron/lesson_history.json` in Blender's config dir.

Current Geometry Nodes topics are derived from the manual HTML tree in:
`https://github.com/murdadrum/Blender50Manual` (blender_manual_v500_en.html/modeling/geometry_nodes).

## Roadmap

- Tutorial runtime (local): UI highlights + deterministic step checks
- Learning Paths (Geometry Nodes) + topic tracking
- Signed lesson packs: versioned, cacheable, offline-friendly
- Auth gateway: OAuth device flow to a future Chiron Cloud Brain
- Multi-model support: Gemini today; pluggable model adapters tomorrow

## License

- Blender add-on: GPL-compatible (required by Blender's licensing for distributed add-ons)
- MCP server: MIT (recommended) or GPL-compatible as needed, depending on linkage and distribution strategy
