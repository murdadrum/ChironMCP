bl_info = {
    "name": "ChironMCP",
    "author": "murdadrum",
    "version": (0, 1, 18),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Chiron",
    "description": "Thin GPL-friendly gateway addon for Chiron tutorial UI + MCP bridge.",
    "category": "3D View",
}

import bpy
from . import learning_paths, lesson_runtime, operators, ui

class CHIRON_Preferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    enable_path_modeling_geometry_nodes: bpy.props.BoolProperty(
        name="Geometry Nodes",
        description="Enable Modeling > Geometry Nodes learning path",
        default=True,
    )

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        icon = "CHECKMARK" if wm.chiron_server_ok else "ERROR"
        layout.label(text=f"Server: {wm.chiron_server_status}", icon=icon)
        layout.operator("chiron.ping_server", icon="URL")
        layout.separator()
        layout.label(text="Learning Paths")
        box = layout.box()
        box.label(text="Modeling")
        box.prop(self, "enable_path_modeling_geometry_nodes", text="Geometry Nodes")


classes = (
    CHIRON_Preferences,
    operators.CHIRON_OT_ping_server,
    operators.CHIRON_OT_send_toast,
    operators.CHIRON_OT_send_highlight,
    # Diagram UI disabled for now.
    # operators.CHIRON_OT_diagram_fetch,
    operators.CHIRON_OT_source_generate,
    operators.CHIRON_OT_lesson_generate,
    operators.CHIRON_OT_lesson_history_reset,
    operators.CHIRON_OT_lesson_start,
    operators.CHIRON_OT_lesson_prev,
    operators.CHIRON_OT_lesson_next,
    operators.CHIRON_OT_lesson_hint,
    operators.CHIRON_OT_lesson_show_me,
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
    bpy.types.WindowManager.chiron_lesson_id = bpy.props.StringProperty(
        name="Chiron Lesson ID",
        default=lesson_runtime.DEFAULT_LESSON_ID,
    )
    bpy.types.WindowManager.chiron_source_url = bpy.props.StringProperty(
        name="Chiron Source URL",
        default="",
    )
    bpy.types.WindowManager.chiron_source_use_llm = bpy.props.BoolProperty(
        name="Chiron Source Use LLM",
        default=True,
    )
    bpy.types.WindowManager.chiron_source_status = bpy.props.StringProperty(
        name="Chiron Source Status",
        default="",
    )
    bpy.types.WindowManager.chiron_active_learning_path = bpy.props.EnumProperty(
        name="Chiron Learning Path",
        items=learning_paths.learning_path_items,
    )
    bpy.types.WindowManager.chiron_active_topic = bpy.props.EnumProperty(
        name="Chiron Topic",
        items=learning_paths.topic_items,
    )
    bpy.types.WindowManager.chiron_current_topic_key = bpy.props.StringProperty(
        name="Chiron Current Topic",
        default="",
    )
    bpy.types.WindowManager.chiron_topic_status = bpy.props.StringProperty(
        name="Chiron Topic Status",
        default="Select a topic",
    )
    bpy.types.WindowManager.chiron_step_index = bpy.props.IntProperty(
        name="Chiron Step Index",
        default=0,
        min=0,
    )
    bpy.types.WindowManager.chiron_step_status = bpy.props.StringProperty(
        name="Chiron Step Status",
        default="Not started",
    )
    bpy.types.WindowManager.chiron_step_hint = bpy.props.StringProperty(
        name="Chiron Step Hint",
        default="",
    )
    # Diagram UI disabled for now.
    # bpy.types.WindowManager.chiron_diagram_image = bpy.props.StringProperty(
    #     name="Chiron Diagram Image",
    #     default="",
    # )
    # bpy.types.WindowManager.chiron_diagram_status = bpy.props.StringProperty(
    #     name="Chiron Diagram Status",
    #     default="Diagram not loaded",
    # )
    operators.ensure_overlay_handler()
    try:
        lesson_runtime.load_progress_into_wm(bpy.context.window_manager)
    except Exception:
        pass


def unregister():
    del bpy.types.WindowManager.chiron_server_status
    del bpy.types.WindowManager.chiron_server_ok
    del bpy.types.WindowManager.chiron_highlight_target
    del bpy.types.WindowManager.chiron_toast_message
    del bpy.types.WindowManager.chiron_step_hint
    del bpy.types.WindowManager.chiron_step_status
    del bpy.types.WindowManager.chiron_step_index
    del bpy.types.WindowManager.chiron_topic_status
    del bpy.types.WindowManager.chiron_current_topic_key
    del bpy.types.WindowManager.chiron_active_topic
    del bpy.types.WindowManager.chiron_active_learning_path
    del bpy.types.WindowManager.chiron_source_status
    del bpy.types.WindowManager.chiron_source_use_llm
    del bpy.types.WindowManager.chiron_source_url
    del bpy.types.WindowManager.chiron_lesson_id
    # Diagram UI disabled for now.
    # del bpy.types.WindowManager.chiron_diagram_status
    # del bpy.types.WindowManager.chiron_diagram_image
    operators.remove_overlay_handler()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
