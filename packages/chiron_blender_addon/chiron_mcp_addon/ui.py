import json
import textwrap
import bpy

from . import learning_paths, lesson_runtime, lesson_tracking

SHOW_LESSON_PACKS = False
_CHAT_DISPLAY_LIMIT = 8
_CHAT_WRAP_WIDTH = 72


def _load_chat_history(wm):
    raw = wm.chiron_chat_history.strip()
    if not raw:
        return []
    try:
        history = json.loads(raw)
    except Exception:
        return []
    return history if isinstance(history, list) else []


def _wrap_chat_lines(text):
    lines = []
    for raw_line in str(text).splitlines() or [""]:
        wrapped = textwrap.wrap(raw_line, width=_CHAT_WRAP_WIDTH)
        if wrapped:
            lines.extend(wrapped)
        else:
            lines.append("")
    return lines


class CHIRON_PT_panel(bpy.types.Panel):
    bl_label = "Chiron"
    bl_idname = "CHIRON_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Chiron"

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        layout.label(text="Chiron v0.1.18")
        if SHOW_LESSON_PACKS:
            layout.label(text="Learning Paths")
            box = layout.box()
            addon = context.preferences.addons.get(__package__)
            prefs = addon.preferences if addon else None
            enabled_paths = learning_paths.get_enabled_paths(prefs) if prefs else []
            if not enabled_paths:
                box.label(text="Enable learning paths in Preferences")
            else:
                if wm.chiron_active_learning_path not in enabled_paths:
                    wm.chiron_active_learning_path = enabled_paths[0]
                box.prop(wm, "chiron_active_learning_path", text="Path")
                available_topics = learning_paths.available_topic_keys(wm.chiron_active_learning_path)
                if available_topics and wm.chiron_active_topic not in available_topics:
                    wm.chiron_active_topic = available_topics[0]
                box.prop(wm, "chiron_active_topic", text="Topic")
                row = box.row(align=True)
                row.operator("chiron.lesson_generate", icon="PLAY")
                row.operator("chiron.lesson_history_reset", icon="TRASH")
                box.label(text=f"Topic status: {wm.chiron_topic_status}")
                total_topics = len(learning_paths.topics_for_path(wm.chiron_active_learning_path))
                remaining = len(available_topics)
                box.label(text=f"Topics remaining: {remaining} of {total_topics}")
                completed = lesson_tracking.get_completed_topics()
                prefix = f"{wm.chiron_active_learning_path}{learning_paths.TOPIC_KEY_SEP}"
                completed_count = len([key for key in completed if key.startswith(prefix)])
                box.label(text=f"Topics completed: {completed_count}")
            layout.label(text="Tutorial Source")
            box = layout.box()
            box.prop(wm, "chiron_source_url", text="Source URL")
            box.prop(wm, "chiron_source_use_llm", text="Use LLM (if available)")
            box.operator("chiron.source_generate", icon="IMPORT")
            if wm.chiron_source_status:
                box.label(text=wm.chiron_source_status)
            layout.label(text="Lesson")
            box = layout.box()
            if wm.chiron_current_topic_key:
                _, slug = learning_paths.split_topic_key(wm.chiron_current_topic_key)
                if slug:
                    box.label(text=f"Current topic: {learning_paths.topic_label(slug)}")
            row = box.row(align=True)
            row.prop(wm, "chiron_lesson_id", text="Lesson")
            row.operator("chiron.lesson_start", icon="PLAY")
            steps = lesson_runtime.get_lesson_steps(wm.chiron_lesson_id)
            if steps:
                for idx, step in enumerate(steps):
                    if idx < wm.chiron_step_index:
                        step_icon = "CHECKMARK"
                    elif idx == wm.chiron_step_index:
                        step_icon = "RADIOBUT_ON"
                    else:
                        step_icon = "RADIOBUT_OFF"
                    box.label(text=f"{idx + 1}. {step.title}", icon=step_icon)
                current = lesson_runtime.get_step(wm.chiron_lesson_id, wm.chiron_step_index)
                if current:
                    box.label(text=f"Instruction: {current.instruction}")
                else:
                    box.label(text="Instruction: Lesson complete")
            else:
                box.label(text="No steps available")
            box.label(text=f"Status: {wm.chiron_step_status}")
            if wm.chiron_step_hint:
                box.label(text=f"Hint: {wm.chiron_step_hint}")
            box.separator()
            # Diagram UI disabled for now.
            # box.label(text="UI Diagram")
            # box.operator("chiron.diagram_fetch", text="Refresh Diagram", icon="FILE_REFRESH")
            # if wm.chiron_diagram_image:
            #     image = bpy.data.images.get(wm.chiron_diagram_image)
            #     if image:
            #         try:
            #             box.template_preview(image)
            #         except Exception:
            #             box.label(text="Diagram loaded")
            #     else:
            #         box.label(text="Diagram missing")
            # box.label(text=wm.chiron_diagram_status)
            row = box.row(align=True)
            row.operator("chiron.lesson_prev", icon="TRIA_LEFT")
            row.operator("chiron.lesson_next", icon="TRIA_RIGHT")
            row = box.row(align=True)
            row.operator("chiron.lesson_hint", icon="HELP")
            row.operator("chiron.lesson_show_me", icon="PLAY")
        layout.label(text="Chat")
        box = layout.box()
        box.prop(wm, "chiron_chat_model", text="Model")
        box.prop(wm, "chiron_chat_use_context", text="Use Blender Context")
        box.prop(wm, "chiron_chat_prompt", text="Prompt")
        row = box.row(align=True)
        row.operator("chiron.chat_send", icon="PLAY")
        if wm.chiron_chat_status:
            box.label(text=wm.chiron_chat_status)
        history = _load_chat_history(wm)
        if not history:
            box.label(text="No messages yet")
        else:
            for message in history[-_CHAT_DISPLAY_LIMIT:]:
                if not isinstance(message, dict):
                    continue
                entry = box.box()
                role = str(message.get("role", "assistant")).strip()
                if role == "user":
                    header = "You"
                elif role == "system":
                    header = "System"
                else:
                    header = "Chiron"
                entry.label(text=header)
                content = message.get("content", "")
                for line in _wrap_chat_lines(content):
                    entry.label(text=line)
