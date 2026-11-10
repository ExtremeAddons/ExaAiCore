#   #
#    This program is free software; you can redistribute it and/or
#    modify it under the terms of the GNU General Public License
#    as published by the Free Software Foundation; either version
#    of the License, or (at your option) any later version.
#   #
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#   #
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software Foundation,
#    Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#   #
#   Copyright 2019 2026(C) Andrea Donati
#

import json
import os
import queue
import bpy
from .orchestrator import Orchestrator


class EXAAICORE_OT_installer(bpy.types.Operator):
    bl_idname = "exa.install_microservice"
    bl_label = "Install ExaAiCore Engine"
    bl_options = {'REGISTER', 'INTERNAL'}

    install_path: bpy.props.StringProperty(
        name="Install path",
        description="Absolute path to the ExtremeAddons root folder where the microservice installation folder will be created",
        options={'HIDDEN'},
        default="",
    )

    install_progress: bpy.props.FloatProperty(
        name="Installation Progress",
        description="Current installation progress percentage",
        default=0.0,
        min=0.0,
        max=100.0,
        subtype='PERCENTAGE'
    )

    confirm_install: bpy.props.EnumProperty(
        name="Confirm Installation",
        description="Confirm that you want to proceed with the installation",
        items=[
            ('YES', "Yes", "Proceed with installation"),
            ('NO', "No", "Cancel installation")
        ],
        default='NO'
    )

    _timer = None
    orchestrator = None
    _cached_config = None

    def invoke(self, context, event):
        self._load_config()
        self.confirm_install = 'NO'
        return context.window_manager.invoke_props_dialog(self, width=450)

    def _load_config(self):
        """Legge il file di configurazione una sola volta."""
        if self._cached_config is not None:
            return
        config_path = os.path.join(os.path.dirname(__file__), "service_config.json")
        with open(config_path, "r", encoding="utf_8") as file:
            self._cached_config = json.load(file)


    def draw(self, context):
        layout = self.layout

        config = self._cached_config or {}

        layout.separator()
        layout.label(text="Warning: Independent runtimes and assets will be downloaded.", icon='INFO')
        layout.label(text="This process requires an active internet connection.")
        layout.label(text="Files will be extracted to your disk without altering Blender.")

        box = layout.box()
        b_col = box.column(align=True)
        b_col.label(text="Installation Details:", icon='INFO')
        b_col.separator()

        # Visualizzazione universale dei Runtimes
        runtimes = config.get("runtimes", [])
        for runtime in runtimes:
            rt_name = runtime.get("name", "runtime")
            rt_version = runtime.get("version", "")
            b_col.label(text=f"Runtime: {rt_name} version {rt_version}")
            deps = runtime.get("dependencies", [])
            if deps:
                b_col.label(text="Dependencies:")
                for dep in deps:
                    b_col.label(text=f"  {dep}", icon='PACKAGE')

        # Visualizzazione universale degli Asset
        assets = config.get("assets", [])
        if assets:
            b_col.separator()
            b_col.label(text="Assets:")
            for asset in assets:
                ast_name = asset.get("name", "asset")
                ast_dest = asset.get("target_subfolder", "")
                b_col.label(text=f"  {ast_name} -> {ast_dest}", icon='FILE_BACKUP')

        layout.separator()
        layout.label(text="Are you sure you want to proceed?", icon='QUESTION')
        layout.separator()

        row = layout.row()
        row.prop(self, "confirm_install", expand=True)

        layout.separator()

    def execute(self, context):
        if self.confirm_install == 'NO':
            self.report({'INFO'}, "Installation cancelled by user.")
            return {'CANCELLED'}

        base_path = os.path.abspath(os.path.expanduser(self.install_path.strip()))
        if not base_path:
            self.report({'ERROR'}, "The install path must be provided by the caller.")
            return {'CANCELLED'}

        os.makedirs(base_path, exist_ok=True)

        self.orchestrator = Orchestrator(base_path)
        self.orchestrator.start_installation_async()

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.progress_begin(0, 100)
        wm.modal_handler_add(self)

        self.report({'INFO'}, f"Installation started in background at: {base_path}")
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'ESC' and event.value == 'PRESS':
            if self.orchestrator:
                self.orchestrator.request_cancel()
            self.report({'INFO'}, "Installation cancelled by user.")

            context.window_manager.event_timer_remove(self._timer)
            context.window_manager.progress_end()
            context.workspace.status_text_set(None)
            return {'CANCELLED'}

        if self.orchestrator:
            try:
                while True:
                    status, message, progress = self.orchestrator.message_queue.get_nowait()

                    self.install_progress = progress * 100.0
                    context.window_manager.progress_update(self.install_progress)
                    context.workspace.status_text_set(f"ExaAiCore: {message}")

                    if status == "FINISHED":
                        context.window_manager.event_timer_remove(self._timer)
                        context.window_manager.progress_end()
                        context.workspace.status_text_set(None)
                        self.report({'INFO'}, message)
                        return {'FINISHED'}

                    elif status == "ERROR":
                        context.window_manager.event_timer_remove(self._timer)
                        context.window_manager.progress_end()
                        context.workspace.status_text_set(None)
                        self.report({'ERROR'}, message)
                        return {'CANCELLED'}

                    elif status == "CANCELLED":
                        context.window_manager.event_timer_remove(self._timer)
                        context.window_manager.progress_end()
                        context.workspace.status_text_set(None)
                        self.report({'WARNING'}, message)
                        return {'CANCELLED'}

            except queue.Empty:
                pass

        if context.area:
            context.area.tag_redraw()

        return {'PASS_THROUGH'}