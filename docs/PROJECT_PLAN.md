# ChironMCP — Project Plan & Roadmap

## Project Mission

Build a **GPL-respecting Blender gateway** that enables **guided, interactive tutorials and AI-assisted learning**, while keeping Chiron’s pedagogical intelligence, lesson quality, and future AI evolution **maintainable, brand-safe, and defensible**.

---

## Guiding Constraints (Non-Negotiables)

- Blender add-on remains **thin, inspectable, GPL-compatible**
- No arbitrary Python execution in production
- No forced SaaS subscription
- Offline-friendly learning where possible
- Cloud required only for:
  - authentication
  - AI tutoring
  - lesson pack updates

---

## Phase Overview

| Phase | Name                 | Outcome                               |
| ----: | -------------------- | ------------------------------------- |
|     0 | Scaffold & Baseline  | Repo boots, CI green, add-on installs |
|     1 | MCP Connectivity     | Real MCP communication path           |
|     2 | Tutorial Runtime     | Interactive step-based learning       |
|     3 | Lesson Packs v1      | Declarative, cacheable content        |
|     4 | Auth & Gating        | Ethical access control                |
|     5 | AI Tutor Integration | Context-aware learning assistant      |
|     6 | Product Polish       | Public-ready MVP                      |

---

## Phase 0 — Scaffold & Baseline ✅ _(current)_

### Goal

Establish a clean, opinionated foundation Codex can safely build on.

### Deliverables

- [ ] Repo structure initialized
- [ ] MCP server scaffold (FastMCP)
- [ ] Blender add-on scaffold
- [ ] README with philosophy statement
- [ ] Architecture documentation
- [ ] CI pipeline (ruff + pytest)
- [ ] Add-on packaging script

### Success Criteria

- Repo clones cleanly
- CI passes
- Blender add-on installs without errors
- MCP server runs locally

---

## Phase 1 — MCP Connectivity (Local)

### Goal

Establish **real communication** between Blender and MCP server.

### Tasks

- [ ] Decide transport strategy:
  - ⬜ Option A: Embed MCP client in Blender (harder)
  - ⬜ Option B: Add `/health` + `/blender/*` proxy endpoints (recommended)
- [ ] Implement `/health` endpoint on MCP server
- [ ] Implement Blender-side HTTP client utilities
- [ ] Replace placeholder “Ping Server” with real response
- [ ] Handle server-unavailable states gracefully in UI

### Success Criteria

- Blender UI confirms live MCP server connection
- Errors are user-friendly (no stack traces)

---

## Phase 2 — Tutorial Runtime (Local, Deterministic)

### Goal

Enable **interactive, step-based tutorials** inside Blender without LLM guesswork.

### Core Features

- [ ] Local lesson session state
- [ ] Step progression (next / previous)
- [ ] Deterministic step validation
- [ ] Progress persistence (in-memory initially)

### UI Features

- [ ] Lesson step list in Blender panel
- [ ] “Next”, “Hint”, “Show Me” buttons
- [ ] Toast notifications
- [ ] Viewport annotations (draw handlers)
- [ ] UI highlighting primitives

### Success Criteria

- User completes a multi-step lesson
- Steps only advance when requirements are met
- Works offline after lesson load

---

## Phase 3 — Lesson Packs v1 (Declarative Content)

### Goal

Ship **structured learning content** without shipping executable code.

### Lesson Pack Format

- [ ] JSON schema defined
- [ ] Versioned metadata
- [ ] Step definitions:
  - instruction text
  - UI targets
  - expected state checks
  - hints
  - optional “do-it-for-me” actions
- [ ] Local caching
- [ ] Pack integrity check (hash/signature stub)

### Content

- [ ] Core Basics v1:
  - Object creation
  - Transform
  - Material assignment
  - Lighting
  - Render

### Success Criteria

- Lesson packs load from disk
- Can be updated independently of add-on
- No executable Python shipped in packs

---

## Phase 4 — Authentication & Ethical Gating

### Goal

Gate **value**, not Blender.

### Features

- [ ] OAuth device-code login flow
- [ ] Token storage in Blender preferences
- [ ] Entitlement checks for lesson packs
- [ ] Offline behavior:
  - cached lessons still work
  - AI tutoring disabled when offline

### UX Principles

- Clear messaging
- No lockout of Blender functionality
- No spyware or aggressive telemetry

### Success Criteria

- User logs in via browser
- Add-on unlocks owned lesson packs
- Offline mode behaves predictably

---

## Phase 5 — AI Tutor Integration (Cloud Brain)

### Goal

Add **context-aware tutoring** without replacing learning.

### Capabilities

- [ ] “Explain this step”
- [ ] “Why did my step fail?”
- [ ] “Generate a lesson from my current scene”
- [ ] Adaptive hints

### Technical

- [ ] Model adapter abstraction
- [ ] Gemini integration (initial)
- [ ] Prompt templates for pedagogy
- [ ] Rate limiting / cost control

### Guardrails

- Tutor explains _why_, not just _what_
- Tutor suggestions map to deterministic steps

### Success Criteria

- Tutor improves completion rate
- Tutor does not auto-skip learning steps
- Tutor feels like a mentor, not a macro runner

---

## Phase 6 — Product Polish & Public MVP

### Goal

Release a **credible, ethical, defensible MVP**.

### Polish

- [ ] UI consistency
- [ ] Error states
- [ ] Logging (opt-in)
- [ ] Documentation pass
- [ ] Example lessons recorded

### Distribution

- [ ] Add-on ZIP distribution
- [ ] Lesson pack delivery flow
- [ ] License / philosophy page

### Messaging

- “AI tutor for Blender literacy”
- “Learn while doing”
- “No subscriptions. No lock-in.”

### Success Criteria

- First-time user completes a lesson in <15 minutes
- Community feedback is positive
- Clear path to paid lesson packs

---

## Long-Term Extensions (Post-MVP)

- Advanced packs (Geometry Nodes, Animation, Shading)
- Classroom / lab licensing
- Multi-seat activation
- Other DCC integrations using the same MCP + lesson engine
- Community-authored lesson packs (curated)

---

## Project Health Metrics

- Lesson completion rate
- Step failure frequency
- Tutor hint usage
- Offline usage percentage
- Time-to-first-success
- User trust signals (issues, discussions)

---

## One-Sentence Product Definition

> **Chiron is a guided learning system that teaches Blender literacy inside real workflows—using AI as a tutor, not a crutch.**
