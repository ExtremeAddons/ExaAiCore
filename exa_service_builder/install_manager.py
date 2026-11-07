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
#   Copyright 2019-2026(C) Andrea Donati

"""
Module for managing microservice installation
"""


import json
import os
import platform
import subprocess
import tarfile
import urllib.request

from .platform_detector import PlatformDetector

# Global variables for installation status (these are managed by the operator)
install_status = "Idle"
install_error = ""
install_finished = False



def resolve_python_executable(target_dir, sys_key):
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
    """
    Perform the installation in a background thread.
    
    Args:
        base_path (str): The path where the microservice will be installed
    """
    global install_status, install_error, install_finished
    try:
        install_status = "Reading configuration..."
        config_path = os.path.join(os.path.dirname(__file__), "service_config.json")
        with open(config_path, "r") as file:
            config = json.load(file)

        target_dir = os.path.join(base_path, config["target_folder_name"])
        os.makedirs(target_dir, exist_ok=True)

        sys_key, arch_key = PlatformDetector.get_platform_keys()

        install_status = "Fetching manifest from repository..."
        req = urllib.request.Request(config["manifest_url"])
        with urllib.request.urlopen(req) as response:
            manifest = json.loads(response.read().decode())

        download_url = manifest["python_engines"][sys_key][arch_key]
        archive_path = os.path.join(target_dir, "python_engine.tar.gz")

        install_status = "Downloading isolated Python engine..."
        urllib.request.urlretrieve(download_url, archive_path)

        install_status = "Extracting Python engine..."
        with tarfile.open(archive_path, 'r:gz') as tar_ref:
            tar_ref.extractall(target_dir)

        os.remove(archive_path)

        install_status = "Configuring pip and installing packages..."
        python_exe = resolve_python_executable(target_dir, sys_key)
        
        setup_script = os.path.join(target_dir, "microservice_setup.py")
        packages_list = json.dumps(config.get("pip_packages", []))

        setup_code = f"""
import subprocess
import sys

packages = {packages_list}
if packages:
    cmd = [sys.executable, "-m", "pip", "install"] + packages
    subprocess.run(cmd, check=True)
"""

        with open(setup_script, "w") as file:
            file.write(setup_code.strip())

        subprocess.run([python_exe, setup_script], check=True, cwd=target_dir)

        install_status = "Microservice successfully configured."
    except Exception as e:
        install_error = str(e)
        install_status = "Critical error during installation."
    finally:
        install_finished = True


def bootstrap_microservice(base_path):
    """
    Bootstrap a microservice by downloading and installing the Python engine.
    
    Args:
        base_path (str): The path where the microservice will be installed
    """
    config_path = os.path.join(os.path.dirname(__file__), "service_config.json")
    with open(config_path, "r") as file:
        config = json.load(file)

    target_dir = os.path.join(base_path, config["target_folder_name"])
    os.makedirs(target_dir, exist_ok=True)

    sys_key, arch_key = PlatformDetector.get_platform_keys()

    req = urllib.request.Request(config["manifest_url"])
    with urllib.request.urlopen(req) as response:
        manifest = json.loads(response.read().decode())

    download_url = manifest["python_engines"][sys_key][arch_key]
    archive_path = os.path.join(target_dir, "python_engine.tar.gz")

    urllib.request.urlretrieve(download_url, archive_path)

    with tarfile.open(archive_path, 'r:gz') as tar_ref:
        tar_ref.extractall(target_dir)

    os.remove(archive_path)
    
    # Find the Python executable
    python_exe = resolve_python_executable(target_dir, sys_key)
    
    setup_script = os.path.join(target_dir, "microservice_setup.py")
    packages_list = json.dumps(config.get("pip_packages", []))

    setup_code = f"""
import subprocess
import sys

packages = {packages_list}
if packages:
    cmd = [sys.executable, "-m", "pip", "install"] + packages
    subprocess.run(cmd, check=True)
"""

    with open(setup_script, "w") as file:
        file.write(setup_code.strip())

    subprocess.run([python_exe, setup_script], check=True, cwd=target_dir)