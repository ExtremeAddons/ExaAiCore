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
import platform
import urllib.request
import zipfile
import subprocess

install_thread = None
install_status = "Idle"
install_error = ""
install_finished = False


def get_platform_keys():
    os_name = platform.system()
    machine_arch = platform.machine().lower()

    sys_key = os_name
    arch_key = machine_arch

    if os_name == "Windows":
        arch_key = "AMD64" if "64" in machine_arch and "arm" not in machine_arch else "ARM64"
    elif os_name == "Darwin":
        arch_key = "arm64" if "arm" in machine_arch else "x86_64"
    elif os_name == "Linux":
        arch_key = "aarch64" if "arm" in machine_arch or "aarch64" in machine_arch else "x86_64"

    return sys_key, arch_key


def background_installer_task(base_path):
    global install_status, install_error, install_finished
    try:
        install_status = "Reading configuration..."
        config_path = os.path.join(os.path.dirname(__file__), "service_config.json")
        with open(config_path, "r") as file:
            config = json.load(file)

        target_dir = os.path.join(base_path, config["target_folder_name"])
        os.makedirs(target_dir, exist_ok=True)

        sys_key, arch_key = get_platform_keys()

        install_status = "Fetching manifest from repository..."
        req = urllib.request.Request(config["manifest_url"])
        with urllib.request.urlopen(req) as response:
            manifest = json.loads(response.read().decode())

        download_url = manifest["python_engines"][sys_key][arch_key]
        zip_path = os.path.join(target_dir, "python_engine.zip")

        install_status = "Downloading isolated Python engine..."
        urllib.request.urlretrieve(download_url, zip_path)

        install_status = "Extracting Python engine..."
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(target_dir)

        os.remove(zip_path)

        install_status = "Configuring pip and installing packages..."
        executable_ext = ".exe" if sys_key == "Windows" else ""
        python_exe = os.path.join(target_dir, "python" + executable_ext)

        if not os.path.exists(python_exe):
            python_exe = os.path.join(target_dir, "bin", "python" + executable_ext)

        setup_script = os.path.join(target_dir, "microservice_setup.py")
        packages_list = json.dumps(config.get("pip_packages", []))

        setup_code = f"""
        import subprocess
        import sys

        packages = {packages_list}
        if packages:
            cmd = [sys.executable, "-m", "pip", "install"] + packages
            subprocess.run(cmd)
        """

        with open(setup_script, "w") as file:
            file.write(setup_code.strip())

        # The wait command ensures the thread does not close before modules are installed
        subprocess.Popen([python_exe, setup_script]).wait()

        install_status = "Microservice successfully configured."
    except Exception as e:
        install_error = str(e)
        install_status = "Critical error during installation."
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

    _timer = None

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=450)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Warning: An independent Python environment will be downloaded.", icon='INFO')
        layout.label(text="This process requires an active internet connection.")
        layout.label(text="Files will be extracted to your disk without altering Blender.")
        layout.separator()
        layout.label(text="Are you sure you want to proceed?", icon='QUESTION')

    def execute(self, context):
        global install_thread, install_status, install_error, install_finished

        base_path = os.path.abspath(os.path.expanduser(self.install_path.strip()))
        if not base_path:
            self.report({'ERROR'}, "The install path must be provided by the caller.")
            return {'CANCELLED'}

        self.report({'INFO'}, "Creo Cartella")
        os.makedirs(base_path, exist_ok=True)

        install_status = "Starting background process..."
        install_error = ""
        install_finished = False

        install_thread = threading.Thread(target=background_installer_task, args=(base_path,))
        install_thread.daemon = True
        install_thread.start()

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)

        self.report({'INFO'}, "Installation started in background.")
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        global install_status, install_error, install_finished

        if event.type == 'TIMER':
            context.workspace.status_text_set("ExaAiCore: " + install_status)

            if install_finished:
                context.window_manager.event_timer_remove(self._timer)
                context.workspace.status_text_set(None)

                if install_error:
                    self.report({'ERROR'}, "Installation failed: " + install_error)
                    return {'CANCELLED'}
                else:
                    self.report({'INFO'}, "Installation completed successfully!")
                    return {'FINISHED'}

        return {'PASS_THROUGH'}





