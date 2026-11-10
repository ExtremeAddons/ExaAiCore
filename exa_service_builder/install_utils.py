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
Module for installation utilities and common functions
"""

import json
import os
import subprocess
import tarfile
import urllib.request

from .platform_detector import PlatformDetector


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

    # Use python_version from config to determine which Python engine to download
    python_version = config.get("python_version", "3.11.18")

    # Check if the manifest has the specific python version we need
    download_url = None

    # Try to get the URL from the new structure (python_versions -> version -> system -> architecture)
    if "python_versions" in manifest:
        if python_version in manifest["python_versions"]:
            if sys_key in manifest["python_versions"][python_version]:
                if arch_key in manifest["python_versions"][python_version][sys_key]:
                    download_url = manifest["python_versions"][python_version][sys_key][arch_key]

    # If we couldn't find it in the new structure, try the old one for backward compatibility
    if not download_url:
        try:
            download_url = manifest["python_versions"][sys_key][arch_key]
        except (KeyError, TypeError):
            raise Exception(f"Could not find Python engine for {sys_key} {arch_key} in manifest")

    archive_path = os.path.join(target_dir, "python_engine.tar.gz")

    urllib.request.urlretrieve(download_url, archive_path)

    with tarfile.open(archive_path, 'r:gz') as tar_ref:
        tar_ref.extractall(target_dir)

    os.remove(archive_path)

    executable_ext = ".exe" if sys_key == "Windows" else ""
    python_exe = os.path.join(target_dir, "python" + executable_ext)

    if not os.path.exists(python_exe):
        python_exe = os.path.join(target_dir, "bin", "python" + executable_ext)

    setup_script = os.path.join(target_dir, "microservice_setup.py")
    packages_list = json.dumps(config.get("pip_packages", []))

    # Corrected: use the isolated python to install packages
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


def generate_requirements_txt(config_path, output_path):
    """
    Generate a requirements.txt file from the service config.

    Args:
        config_path (str): Path to the service_config.json file
        output_path (str): Path where requirements.txt should be created
    """
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Extract pip packages from config
    pip_packages = config.get('pip_packages', [])

    # Write to requirements.txt
    with open(output_path, 'w') as f:
        for package in pip_packages:
            f.write(f"{package}\n")
