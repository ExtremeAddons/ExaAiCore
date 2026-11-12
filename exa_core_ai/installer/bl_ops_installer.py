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
import shutil

import bpy
from .orchestrator import Orchestrator
from .bl_draw import Draw


class EXAAICORE_OT_installer(bpy.types.Operator):
    bl_idname = "exa.install_microservice"
    bl_label = "Install ExaCoreAi Engine"
    bl_options = {'REGISTER', 'INTERNAL'}

    options: bpy.props.EnumProperty(
        name="Options",
        description="Choose an option",
        items=[
            ('INSTALL', "Install", "Install the microservice"),
            ('UNINSTALL', "Uninstall", "Uninstall the microservice")
        ],
        default='INSTALL'
    )

    install_path: bpy.props.StringProperty(
        name="Install path",
        description="Absolute path to the ExtremeAddons root folder",
        options={'HIDDEN'},
        default="",
    )

    confirm: bpy.props.EnumProperty(
        name="Confirm",
        description="Confirm that you want to proceed",
        items=[
            ('YES', "Yes", "Proceed"),
            ('NO', "No", "Cancel")
        ],
        default='NO'
    )

    _timer = None
    orchestrator = None
    _cached_config = None

    def invoke(self, context, event):
        bpy.types.WindowManager.exa_install_running = bpy.props.BoolProperty(
            name="Is Running",
            default=False
        )
        bpy.types.WindowManager.exa_install_progress = bpy.props.FloatProperty(
            name="Progress",
            default=0.0,
            min=0.0,
            max=100.0,
            subtype='PERCENTAGE'
        )
        bpy.types.WindowManager.exa_install_msg = bpy.props.StringProperty(
            name="Message",
            default=""
        )

        self._load_config()
        self.confirm = 'NO'
        return context.window_manager.invoke_props_dialog(self, width=450)

    def _cleanup_wm_props(self, context):
        wm = context.window_manager
        wm.exa_install_running = False
        wm.exa_install_progress = 0.0
        wm.exa_install_msg = ""

    def _load_config(self):
        if self._cached_config is not None:
            return
        config_path = os.path.join(os.path.dirname(__file__), "../service_config.json")
        with open(config_path, "r", encoding="utf_8") as file:
            self._cached_config = json.load(file)

    def draw(self, context):
        if self.options == 'INSTALL':
            self._popup_install(context)
        elif self.options == 'UNINSTALL':
            self._popup_uninstall(context)

    def _popup_install(self, context):
        layout = self.layout
        layout.separator()
        layout.label(text="Warning: Independent runtimes and assets will be downloaded.", icon='INFO')
        layout.label(text="This process requires an active internet connection.")
        layout.label(text="Files will be extracted to your disk without altering Blender.")

        Draw(extreme_addons_path=self.install_path).draw_requirement_files(layout, use_box=True)

        layout.separator()
        layout.label(text="Are you sure you want to proceed?", icon='QUESTION')
        layout.separator()

        row = layout.row()
        row.prop(self, "confirm", expand=True)
        layout.separator()

    def _popup_uninstall(self, context):
        layout = self.layout
        layout.separator()
        layout.label(text="Warning: This will remove the ExaCoreAi engine and its assets.", icon='ERROR')
        layout.label(text="This process will delete files from your disk.")
        layout.label(text="Are you sure you want to proceed?")
        layout.separator()

        row = layout.row()
        row.prop(self, "confirm", expand=True)
        layout.separator()

    def execute(self, context):
        if self.options == 'INSTALL':
            return self._install(context)
        elif self.options == 'UNINSTALL':
            return self._uninstall(context)
        return {'FINISHED'}

    def _cleanup(self, context):
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
        self._cleanup_wm_props(context)
        if context.area:
            context.area.tag_redraw()

    def _install(self, context):
        if self.confirm == 'NO':
            self._cleanup_wm_props(context)
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
        wm.exa_install_running = True
        wm.exa_install_progress = 0.0
        wm.exa_install_msg = "Starting installation..."

        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)

        self.report({'INFO'}, f"Installation started in background at: {base_path}")
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'ESC' and event.value == 'PRESS':
            if self.orchestrator:
                self.orchestrator.request_cancel()
            self._cleanup(context)
            self.report({'INFO'}, "Installation cancelled by user.")
            return {'CANCELLED'}

        if event.type == 'TIMER':
            if self.orchestrator:
                try:
                    while True:
                        status, message, progress = self.orchestrator.message_queue.get_nowait()

                        wm = context.window_manager
                        wm.exa_install_progress = float(progress) * 100.0
                        wm.exa_install_msg = message

                        if status == "FINISHED":
                            self._cleanup(context)
                            self.report({'INFO'}, message)
                            return {'FINISHED'}

                        elif status == "ERROR":
                            self._cleanup(context)
                            self.report({'ERROR'}, message)
                            return {'CANCELLED'}

                        elif status == "CANCELLED":
                            self._cleanup(context)
                            self.report({'WARNING'}, message)
                            return {'CANCELLED'}

                except queue.Empty:
                    pass

            if context.area:
                context.area.tag_redraw()

        return {'PASS_THROUGH'}

    def _uninstall(self, context):
        if self.confirm == 'NO':
            self._cleanup_wm_props(context)
            self.report({'INFO'}, "Uninstallation cancelled by user.")
            return {'CANCELLED'}

        base_path = os.path.abspath(os.path.expanduser(self.install_path.strip()))
        if not base_path:
            self._cleanup_wm_props(context)
            self.report({'ERROR'}, "Install path is missing.")
            return {'CANCELLED'}

        target_dir = os.path.join(base_path, "ExaCoreAi")

        if os.path.exists(target_dir):
            try:
                shutil.rmtree(target_dir)
                self.report({'INFO'}, "ExaCoreAi engine removed successfully.")
            except Exception as error:
                self.report({'ERROR'}, f"Failed to remove folder: {error}")
                self._cleanup_wm_props(context)
                return {'CANCELLED'}

        self._cleanup_wm_props(context)
        return {'FINISHED'}