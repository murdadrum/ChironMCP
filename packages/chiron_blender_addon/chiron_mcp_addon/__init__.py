bl_info = {
    "name": "ChironMCP",
    "author": "murdadrum",
    "version": (0, 1, 12),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Chiron",
    "description": "Thin GPL-friendly gateway addon for Chiron tutorial UI + MCP bridge.",
    "category": "3D View",
}

import bpy
from . import operators, ui

classes = (
    operators.CHIRON_OT_ping_server,
    operators.CHIRON_OT_send_toast,
    operators.CHIRON_OT_send_highlight,
    ui.CHIRON_PT_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.WindowManager.chiron_server_ok = bpy.props.BoolProperty(
        name="Chiron Server OK",
        default=False,
    )
    bpy.types.WindowManager.chiron_server_status = bpy.props.StringProperty(
        name="Chiron Server Status",
        default="Unknown",
    )
    bpy.types.WindowManager.chiron_toast_message = bpy.props.StringProperty(
        name="Chiron Toast Message",
        default="Hello from Blender",
    )
    bpy.types.WindowManager.chiron_highlight_target = bpy.props.StringProperty(
        name="Chiron Highlight Target",
        default="VIEW_3D",
    )
    operators.ensure_overlay_handler()


def unregister():
    del bpy.types.WindowManager.chiron_server_status
    del bpy.types.WindowManager.chiron_server_ok
    del bpy.types.WindowManager.chiron_highlight_target
    del bpy.types.WindowManager.chiron_toast_message
    operators.remove_overlay_handler()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
