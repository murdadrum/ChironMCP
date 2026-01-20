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
