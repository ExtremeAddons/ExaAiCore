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

import bpy
import threading
import os
import json
import urllib.request
import tarfile
import subprocess

from .platform_detector import PlatformDetector

install_thread = None
install_status = "Idle"
install_error = ""
install_finished = False
install_progress = 0


def resolve_python_executable(target_dir, sys_key):
    """Find the Python executable bundled in the extracted engine."""
    executable_names = [
        "python.exe" if sys_key == "Windows" else "python",
        "python3.exe" if sys_key == "Windows" else "python3",
    ]

    candidates = []
    for root, _, files in os.walk(target_dir):
        for file_name in files:
            lower_name = file_name.lower()
            if lower_name in {name.lower() for name in executable_names}:
                candidates.append(os.path.join(root, file_name))

    for candidate in candidates:
        if os.path.isfile(candidate):
            if os.name != "nt":
                try:
                    current_mode = os.stat(candidate).st_mode
                    os.chmod(candidate, current_mode | 0o111)
                except OSError:
                    pass
            return candidate

    raise FileNotFoundError(
        "Bundled Python executable was not found in the extracted engine folder. "
        "The archive layout is different from the expected default structure."
    )


def background_installer_task(base_path):
    """Install the isolated Python engine without blocking Blender's UI."""
    global install_status, install_error, install_finished, install_progress
    try:
        install_status = "Reading configuration..."
        install_progress = 2
        config_path = os.path.join(os.path.dirname(__file__), "service_config.json")
        with open(config_path, "r") as file:
            config = json.load(file)

        target_dir = os.path.join(base_path, config["target_folder_name"])
        os.makedirs(target_dir, exist_ok=True)

        sys_key, arch_key = PlatformDetector.get_platform_keys()

        install_status = "Fetching manifest from repository..."
        install_progress = 7
        req = urllib.request.Request(config["manifest_url"])
        with urllib.request.urlopen(req) as response:
            manifest = json.loads(response.read().decode())

        download_url = manifest["python_engines"][sys_key][arch_key]
        archive_path = os.path.join(target_dir, "python_engine.tar.gz")

        install_status = "Downloading isolated Python engine..."
        install_progress = 10

        def update_download_progress(block_count, block_size, total_size):
            """Map download progress to the first part of the installation bar."""
            global install_progress
            if total_size > 0:
                downloaded = block_count * block_size
                install_progress = 10 + min(35, int(downloaded * 35 / total_size))

        urllib.request.urlretrieve(
            download_url,
            archive_path,
            reporthook=update_download_progress,
        )

        install_status = "Extracting Python engine..."
        install_progress = 50
        with tarfile.open(archive_path, 'r:gz') as tar_ref:
            tar_ref.extractall(target_dir)

        os.remove(archive_path)
        install_progress = 60

        install_status = "Configuring pip and installing packages..."
        install_progress = 65
        python_exe = resolve_python_executable(target_dir, sys_key)

        packages = config.get("pip_packages", [])
        if packages:
            process = subprocess.Popen(
                [python_exe, "-m", "pip", "install", "--progress-bar", "off"] + packages,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=target_dir,
            )
            recent_output = []
            for line in process.stdout:
                output = line.strip()
                if not output:
                    continue
                recent_output.append(output)
                del recent_output[:-5]

                if output.startswith("Collecting "):
                    package_name = output[len("Collecting "):].split()[0]
                    install_status = f"Resolving package: {package_name}"
                    install_progress = max(install_progress, 70)
                elif output.startswith("Downloading ") or output.startswith("Using cached "):
                    install_status = "Downloading Python packages..."
                    install_progress = max(install_progress, 75)
                elif output.startswith("Installing collected packages"):
                    install_status = "Installing Python packages..."
                    install_progress = max(install_progress, 90)
                elif output.startswith("Successfully installed "):
                    install_status = "Finishing package installation..."
                    install_progress = max(install_progress, 98)

            return_code = process.wait()
            if return_code:
                details = "\n".join(recent_output)
                raise RuntimeError(
                    f"Package installation failed with exit code {return_code}."
                    + (f"\n{details}" if details else "")
                )

        install_status = "Microservice successfully configured."
        install_progress = 100
    except Exception as e:
        install_error = str(e)
        install_status = f"Critical error during installation: {str(e)}"
    finally:
        install_finished = True


class EXAAICORE_OT_install_microservice(bpy.types.Operator):
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
        return context.window_manager.invoke_props_dialog(self, width=450)

    def draw(self, context):
        """Draw the installation confirmation dialog."""
        layout = self.layout
        col = layout.column()
        
        # Add a more detailed status display in the dialog 
        if install_status != "Idle":
            row = col.row(align=True)
            row.label(text="Installation Status:", icon='INFO')
            
            sub_col = row.column()  
            sub_col.scale_y = 0.8
            sub_col.label(text=install_status, icon_value=get_icon_for_status(install_status))
            
            # Add progress bar for installation
            if install_progress > 0:
                row = col.row()
                row.prop(self, "install_progress", text="Progress")
        
        layout.separator()
        layout.label(text="Warning: An independent Python environment will be downloaded.", icon='INFO') 
        layout.label(text="This process requires an active internet connection.")
        layout.label(text="Files will be extracted to your disk without altering Blender.")
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

        global install_thread, install_status, install_error, install_finished, install_progress

        base_path = os.path.abspath(os.path.expanduser(self.install_path.strip()))
        if not base_path:
            self.report({'ERROR'}, "The install path must be provided by the caller.")
            return {'CANCELLED'}

        # Clear previous installation state
        install_status = ""
        install_error = "" 
        install_finished = False
        install_progress = 0

        os.makedirs(base_path, exist_ok=True)

        install_status = "Starting background process..."
        
        self.report({'INFO'}, f"Installation started in background at: {base_path}")

        install_thread = threading.Thread(target=background_installer_task, args=(base_path,))
        install_thread.daemon = True
        install_thread.start()

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.progress_begin(0, 100)
        wm.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        """Refresh Blender's visible installation progress and handle completion."""
        global install_status, install_error, install_finished, install_progress

        if event.type == 'TIMER':
            # Update the progress property for the UI
            self.install_progress = install_progress
            
            if not install_finished:
                current_status = f"ExaAiCore: {install_status} ({install_progress}%)"
            elif not install_error:
                current_status = "ExaAiCore: Installation complete."
            else:
                current_status = f"ExaAiCore: Installation failed: {install_error[:100]}"

            context.workspace.status_text_set(current_status)
            context.window_manager.progress_update(install_progress)
            if context.area:
                context.area.tag_redraw()

            if install_finished:
                context.window_manager.event_timer_remove(self._timer)
                context.window_manager.progress_end()
                context.workspace.status_text_set(None)

                if install_error:
                    self.report({'ERROR'}, f"Installation failed: {install_error}")
                    
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

