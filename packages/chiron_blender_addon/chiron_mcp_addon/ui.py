import bpy


class CHIRON_PT_panel(bpy.types.Panel):
    bl_label = "Chiron"
    bl_idname = "CHIRON_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Chiron"

    def draw(self, context):
        layout = self.layout
        layout.label(text="ChironMCP (dev scaffold)")
        layout.operator("chiron.ping_server", icon="URL")
