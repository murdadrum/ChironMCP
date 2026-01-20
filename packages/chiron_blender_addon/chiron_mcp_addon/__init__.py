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
