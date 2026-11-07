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
Module for platform detection and system information
"""

import platform
import sys
from typing import Tuple


class PlatformDetector:
    """
    A class to detect and manage platform-specific information including
    operating system and architecture.
    """

    @staticmethod
    def get_platform_keys() -> Tuple[str, str]:
        """
        Detects the platform keys (system key and architecture key)
        based on the current operating system and machine architecture.
        
        Returns:
            Tuple[str, str]: A tuple containing (sys_key, arch_key) where:
                - sys_key: The system identifier (Windows, Darwin, Linux)
                - arch_key: The architecture identifier (AMD64, ARM64, x86_64, arm64, aarch64)
        """
        # Get the operating system name
        os_name = platform.system()
        
        # Get the machine architecture and convert to lowercase for comparison
        machine_arch = platform.machine().lower()
        
        # Initialize keys
        sys_key = os_name
        arch_key = machine_arch
        
        # Map the architecture based on OS
        if os_name == "Windows":
            # For Windows, map common architectures to our expected keys
            if "64" in machine_arch and "arm" not in machine_arch:
                arch_key = "AMD64"
            elif "arm" in machine_arch:
                arch_key = "ARM64"
            else:
                # Default fallback for Windows
                arch_key = "AMD64"  # Assume 64-bit as default
        
        elif os_name == "Darwin":  # macOS
            if "arm" in machine_arch:
                arch_key = "arm64"
            elif "x86_64" in machine_arch:
                arch_key = "x86_64"
            else:
                # Default fallback for macOS
                arch_key = "arm64"  # Assume Apple Silicon as default
        
        elif os_name == "Linux":
            if "arm" in machine_arch or "aarch64" in machine_arch:
                arch_key = "aarch64"
            elif "x86_64" in machine_arch:
                arch_key = "x86_64"
            else:
                # Default fallback for Linux
                arch_key = "x86_64"  # Assume x86_64 as default
        
        return sys_key, arch_key

    @staticmethod
    def get_system_info() -> dict:
        """
        Get comprehensive system information.
        
        Returns:
            dict: A dictionary containing system information
        """
        return {
            "platform": platform.platform(),
            "system": platform.system(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "architecture": platform.architecture()[0],
            "python_version": sys.version,
            "python_platform": sys.platform
        }

    @staticmethod
    def validate_platform() -> bool:
        """
        Validates if the current platform is supported.
        
        Returns:
            bool: True if platform is supported, False otherwise
        """
        try:
            sys_key, arch_key = PlatformDetector.get_platform_keys()
            
            # Check if we support this combination
            supported_platforms = {
                "Windows": ["AMD64", "ARM64"],
                "Darwin": ["arm64", "x86_64"],
                "Linux": ["aarch64", "x86_64"]
            }
            
            if sys_key in supported_platforms:
                return arch_key in supported_platforms[sys_key]
            else:
                return False
                
        except Exception:
            # If we can't detect platform, assume not supported
            return False


# Example usage (can be removed in production)
# if __name__ == "__main__":
#     detector = PlatformDetector()
#     print("Platform Keys:", detector.get_platform_keys())
#     print("System Info:", detector.get_system_info())
#     print("Is Valid Platform:", detector.validate_platform())