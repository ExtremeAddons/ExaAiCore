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




import os
import json
import platform
import urllib.request
import zipfile
import subprocess


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


def bootstrap_microservice(base_path):
    config_path = os.path.join(os.path.dirname(__file__), "service_config.json")
    with open(config_path, "r") as file:
        config = json.load(file)

    target_dir = os.path.join(base_path, config["target_folder_name"])
    os.makedirs(target_dir, exist_ok=True)

    sys_key, arch_key = get_platform_keys()

    req = urllib.request.Request(config["manifest_url"])
    with urllib.request.urlopen(req) as response:
        manifest = json.loads(response.read().decode())

    download_url = manifest["python_engines"][sys_key][arch_key]
    zip_path = os.path.join(target_dir, "python_engine.zip")

    urllib.request.urlretrieve(download_url, zip_path)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(target_dir)

    os.remove(zip_path)

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
for pkg in packages:
    subprocess.run([sys.executable, "-m", "pip", "install", pkg])
"""
    with open(setup_script, "w") as file:
        file.write(setup_code.strip())

    subprocess.Popen([python_exe, setup_script])