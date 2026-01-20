import bpy


class CHIRON_PT_panel(bpy.types.Panel):
    bl_label = "Chiron"
    bl_idname = "CHIRON_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Chiron"

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        layout.label(text="ChironMCP (dev scaffold v0.1.12)")
        icon = "CHECKMARK" if wm.chiron_server_ok else "ERROR"
        layout.label(text=f"Server: {wm.chiron_server_status}", icon=icon)
        layout.operator("chiron.ping_server", icon="URL")
        layout.separator()
        layout.label(text="Demo")
        layout.prop(wm, "chiron_toast_message", text="Toast")
        layout.operator("chiron.send_toast", icon="INFO")
        layout.prop(wm, "chiron_highlight_target", text="Highlight")
        layout.operator("chiron.send_highlight", icon="RESTRICT_SELECT_OFF")
