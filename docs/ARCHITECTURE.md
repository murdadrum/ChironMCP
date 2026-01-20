# Architecture

## Principle
Blender add-on = thin "gateway" (GPL-friendly)
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
