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
#


"""
Module for managing background installation tasks
"""

import json
import os
import subprocess
import tarfile
import urllib.request

from .config_reader import ConfigReader
from .platform_detector import PlatformDetector
from .install_utils import resolve_python_executable


class BackgroundInstaller:
    """
    A class to manage background installation of microservice Python engines.
    """

    def __init__(self):
        """Initialize the background installer."""
        self.install_status = "Idle"
        self.install_error = ""
        self.install_finished = False
        self.install_progress = 0
        self.current_download_url = ""
        self.install_cancelled = False

    def background_installer_task(self, base_path):
        """
        Install the isolated Python engine without blocking Blender's UI.

        Args:
            base_path (str): The path where the microservice will be installed
        """
        try:
            self.install_status = "Reading configuration..."
            config = ConfigReader.get_config_data(base_path)
            target_dir = config["target_dir"]

            # Ensure target directory exists
            os.makedirs(target_dir, exist_ok=True)

            sys_key, arch_key = PlatformDetector.get_platform_keys()

            self.install_status = "Fetching manifest from repository..."
            self.install_progress = 7
            # Check for cancellation before proceeding
            if self.install_cancelled:
                raise RuntimeError("Installation cancelled by user")

            try:
                req = urllib.request.Request(config["manifest_url"])
                # Add timeout to prevent hanging on network issues
                with urllib.request.urlopen(req, timeout=30) as response:
                    manifest = json.loads(response.read().decode())
            except urllib.error.URLError as e:
                raise RuntimeError(f"Failed to fetch manifest from {config['manifest_url']}: {str(e)}")
            except json.JSONDecodeError as e:
                raise RuntimeError(f"Invalid JSON in manifest from {config['manifest_url']}: {str(e)}")
            except Exception as e:
                raise RuntimeError(f"Unexpected error fetching manifest: {str(e)}")

            print(f"Manifest fetched: {manifest}")  # Debugging line
            python_version = config["python_version"]
            download_url = manifest[python_version][sys_key][arch_key]
            self.current_download_url = download_url
            archive_path = os.path.join(target_dir, "python_engine.tar.gz")

            self.install_status = "Downloading isolated Python engine..."
            self.install_progress = 10

            def update_download_progress(block_count, block_size, total_size):
                """Map download progress to the first part of the installation bar."""
                # Check for cancellation during download
                if self.install_cancelled:
                    raise RuntimeError("Installation cancelled by user")
                    
                if total_size > 0:
                    downloaded = block_count * block_size
                    self.install_progress = 10 + min(35, int(downloaded * 35 / total_size))

            urllib.request.urlretrieve(
                download_url,
                archive_path,
                reporthook=update_download_progress,
            )

            self.install_status = "Extracting Python engine..."
            self.install_progress = 50
            with tarfile.open(archive_path, 'r:gz') as tar_ref:
                tar_ref.extractall(target_dir)

            os.remove(archive_path)
            self.install_progress = 60

            self.install_status = "Configuring pip and installing packages..."
            self.install_progress = 65
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
                    # Check for cancellation during package installation
                    if self.install_cancelled:
                        process.terminate()
                        raise RuntimeError("Installation cancelled by user")
                        
                    output = line.strip()
                    if not output:
                        continue
                    recent_output.append(output)
                    del recent_output[:-5]

                    if output.startswith("Collecting "):
                        package_name = output[len("Collecting "):].split()[0]
                        self.install_status = f"Resolving package: {package_name}"
                        self.install_progress = max(self.install_progress, 70)
                    elif output.startswith("Downloading ") or output.startswith("Using cached "):
                        self.install_status = "Downloading Python packages..."
                        self.install_progress = max(self.install_progress, 75)
                    elif output.startswith("Installing collected packages"):
                        self.install_status = "Installing Python packages..."
                        self.install_progress = max(self.install_progress, 90)
                    elif output.startswith("Successfully installed "):
                        self.install_status = "Finishing package installation..."
                        self.install_progress = max(self.install_progress, 98)

                return_code = process.wait()
                if return_code:
                    details = "\n".join(recent_output)
                    raise RuntimeError(
                        f"Package installation failed with exit code {return_code}."
                        + (f"\n{details}" if details else "")
                    )

            self.install_status = "Microservice successfully configured."
            self.install_progress = 100
        except Exception as e:
            print("Error during installation:", str(e))  # Debugging line
            # Include URL information in error message when available
            error_message = str(e)
            if self.current_download_url:
                error_message = f"Error accessing URL '{self.current_download_url}': {error_message}"
            self.install_error = error_message
            self.install_status = f"Critical error during installation: {error_message}"
        finally:
            print("Installation task completed. Final status:", self.install_status)  # Debugging line
            self.install_finished = True
