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


import json
import os
import subprocess
import urllib.request
import tarfile

from .platform_detector import PlatformDetector


def bootstrap_microservice(base_path):
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
    
    # Get the specific Python version's engine URLs from manifest
    download_url = None
    
    # Try to get the URL from the new structure with python_versions mapping
    if "python_versions" in manifest:
        if python_version in manifest["python_versions"]:
            if sys_key in manifest["python_versions"][python_version]:
                if arch_key in manifest["python_versions"][python_version][sys_key]:
                    download_url = manifest["python_versions"][python_version][sys_key][arch_key]
    
    # If we couldn't find it, try the old structure for backward compatibility
    if not download_url:
        try:
            download_url = manifest["python_engines"][sys_key][arch_key]
        except (KeyError, TypeError):
            raise Exception(f"Could not find Python engine for {python_version} on {sys_key} {arch_key}")

    if not download_url:
        raise Exception(f"Could not find Python engine URL for {python_version} on {sys_key} {arch_key}")

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