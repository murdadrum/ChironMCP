import json
import urllib.request

import bpy

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
