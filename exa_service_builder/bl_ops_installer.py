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
import threading

import bpy

from .background_installer import BackgroundInstaller

# Create an instance of the background installer
b_i = BackgroundInstaller()


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

    def invoke(self, context, event):
        """Ask the user to confirm before starting the installation."""
        self.confirm_install = 'NO'
        return context.window_manager.invoke_props_dialog(self, width=450)

    def draw(self, context):
        """Draw the installation confirmation dialog."""
        layout = self.layout
        
        # Show what will be installed
        config_path = os.path.join(os.path.dirname(__file__), "service_config.json")
        with open(config_path, "r") as file:
            config = json.load(file)

        layout.separator()
        layout.label(text="Warning: An independent Python environment will be downloaded.", icon='INFO') 
        layout.label(text="This process requires an active internet connection.")
        layout.label(text="Files will be extracted to your disk without altering Blender.")

        # Add a section for what will be installed
        box = layout.box()
        b_col = box.column(align=True)
        b_col.label(text="Installation Details:", icon='INFO')
        b_col.separator()

        # Show Python version
        if "python_version" in config:
            b_col.label(text=f"Python Version: {config['python_version']}")

        # Show pip packages to be installed
        packages = config.get("pip_packages", [])
        if packages:
            b_col.label(text="Pip Packages:")
            for package in packages:
                b_col.label(text=f"  • {package}", icon='PACKAGE')

        layout.separator()
        layout.label(text="Are you sure you want to proceed?", icon='QUESTION')
        layout.separator()

        # Add confirmation property
        row = layout.row()
        row.prop(self, "confirm_install", expand=True)

        layout.separator()

    def execute(self, context):
        """Start the background installer and monitor it with a modal timer."""
        # Check if user confirmed installation
        if self.confirm_install == 'NO':
            self.report({'INFO'}, "Installation cancelled by user.")
            return {'CANCELLED'}

        base_path = os.path.abspath(os.path.expanduser(self.install_path.strip()))
        if not base_path:
            self.report({'ERROR'}, "The install path must be provided by the caller.")
            return {'CANCELLED'}

        # Clear previous installation state using instance properties
        b_i.install_thread = None
        b_i.install_status = "Idle"
        b_i.install_error = ""
        b_i.install_finished = False
        b_i.install_progress = 0
        b_i.current_download_url = ""

        os.makedirs(base_path, exist_ok=True)

        b_i.install_status = "Starting background process..."

        self.report({'INFO'}, f"Installation started in background at: {base_path}")

        b_i.install_thread = threading.Thread(target=b_i.background_installer_task, args=(base_path,))
        b_i.install_thread.daemon = True
        b_i.install_thread.start()

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.progress_begin(0, 100)
        wm.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        """Refresh Blender's visible installation progress and handle completion."""
        # Handle ESC key press to cancel the operation
        if event.type == 'ESC' and event.value == 'PRESS':
            self.report({'INFO'}, "Installation cancelled by user (ESC pressed).")

            # Cancel the installation process
            b_i.install_cancelled = True

            # Remove timer and clean up
            context.window_manager.event_timer_remove(self._timer)
            context.window_manager.progress_end()
            context.workspace.status_text_set(None)

            return {'CANCELLED'}

        if event.type == 'TIMER':
            # Update the progress property for the UI using instance properties
            self.install_progress = b_i.install_progress

            if not b_i.install_finished:
                current_status = f"ExaAiCore: {b_i.install_status} ({b_i.install_progress}%)"
            elif not b_i.install_error:
                current_status = "ExaAiCore: Installation complete."
            else:
                current_status = f"ExaAiCore: Installation failed: {b_i.install_error[:100]}"

            context.workspace.status_text_set(current_status)
            context.window_manager.progress_update(b_i.install_progress)
            if context.area:
                context.area.tag_redraw()

            if b_i.install_finished:
                context.window_manager.event_timer_remove(self._timer)
                context.window_manager.progress_end()
                context.workspace.status_text_set(None)

                if b_i.install_error:
                    self.report({'ERROR'}, f"Installation failed: {b_i.install_error} current url: {b_i.current_download_url}")

                    return {'CANCELLED'}
                else:
                    self.report({'INFO'}, "Installation completed successfully!")

                    return {'FINISHED'}

        return {'PASS_THROUGH'}


def get_icon_for_status(status_text):
    """Return an icon appropriate for the current installation status."""
    if 'error' in status_text.lower():
        return 179   # Error icon
    elif any(word in status_text.lower() for word in ['downloading', 'extracting']):
        return 243   # Download/progress indicator  
    else:
        return 608     # Default info icon
