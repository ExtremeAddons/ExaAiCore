# ExaAiCore

## Overview

ExaAiCore is a modular architecture designed to deploy and manage isolated Python environments called microservices for Blender addons like HDRi Maker. The primary goal is to run heavy AI frameworks such as PyTorch and Diffusers in a completely separate process, preventing dependency conflicts with Blender's native Python interpreter and avoiding UI blocking or crashes.

## Architecture

### Remote Repository
A GitHub repository that hosts ZIP files containing standalone Python engines for Windows, macOS, and Linux, accompanied by an `exa_manifest.json` file that maps direct download URLs.

### Local Bootstrapper
The `exa_service_builder` module integrated into the Blender addon. It contains:
- `service_config.json`: Configuration file for service settings
- `installer.py`: Pure Python script for network logic and extraction
- `installer_ops.py`: Blender interface for user interaction

### Microservice Worker
A Python script that runs physically within the isolated environment. It handles loading AI models, processing data, and returning results to Blender.

## Key Features

- **Engineering Separation**: Maintain clear distinction between Blender-specific code (based on bpy) and standard Python logic. Network, extraction, and isolated worker code must have no dependencies on Blender's internal libraries.
- **Asynchronous Execution**: No heavy operations like download, installation, or AI computation should ever block Blender's main thread. Use threading and modal operators with timers for UI updates.
- **Environmental Isolation**: All package installations via pip must be scoped to the microservice folder. Use the subprocess module to invoke the isolated Python executable, passing concatenated library lists in a single command to optimize dependency resolution.
- **Dynamic Path Management**: Never hardcode absolute paths in code or JSON files. Always use `os.path` to construct paths at runtime based on the actual addon location on the user's computer.
- **Interprocess Communication**: Parameter and result passing between Blender and the isolated engine must occur via standardized JSON strings. Use `sys.argv`, temporary files, or reading standard output through subprocess.Popen, including advanced exception handling and timeout management for external engine crashes.

## Configuration

### service_config.json

The `service_config.json` file is crucial for customizing ExaAiCore to your specific application needs. This configuration file must be personalized by applications that intend to use ExaAiCore, as it defines:

- Required core version
- Manifest URL for downloading the appropriate Python engine
- Target folder name for installation
- Python version to use
- Pip packages required for the microservice

Each application using ExaAiCore should modify this file according to its specific requirements and dependencies.

## Development Guidelines

- **Import Structure**: When importing functions, classes, or any other elements from within the project, always use relative imports (e.g., `from .module import function`).
- **Code Documentation**: Write clean, modular, production-oriented code, preferring Python's standard library for base functions and avoiding unnecessary external dependencies in the bootstrapper.
- **Code Comments**: Always comment your code clearly in English.
- **Docstrings**: Use docstrings for all functions, classes, and methods following PEP 257 standards, strictly in English.

## License

This project is licensed under the GNU General Public License v3.0 - see the LICENSE file for details.
