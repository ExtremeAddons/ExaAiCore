# ExaCoreAi

## Overview

ExaCoreAi is a modular architecture designed to deploy and manage isolated Python environments called microservices for Blender add-ons, particularly for advanced AI-powered tools like HDRi Maker. The primary goal is to execute heavy AI frameworks such as PyTorch and Diffusers in completely separate processes, preventing dependency conflicts with Blender's native Python interpreter and avoiding UI blocking or crashes.

## Architecture

### Core Components

1. **Remote Repository**: GitHub repository hosting standalone Python engines for Windows, macOS, and Linux, accompanied by an `exa_manifest.json` file that maps direct download URLs.
2. **Local Bootstrapper**: Folder `exa_service_builder` containing:
   - `service_config.json`: Configuration file for the service
   - Pure Python installer script (`installer.py`): Network and extraction logic
   - Blender interface integration (`installer_ops.py`): User interaction with Blender
3. **Microservice Worker**: A Python script that runs within the isolated environment, responsible for loading AI models, processing data, and returning results to Blender.

## Key Features

- **Engine Isolation**: Complete separation of AI processing from Blender's main process
- **Dependency Management**: Independent package installations using pip in isolated environments
- **Cross-Platform Support**: Native support for Windows, macOS, and Linux
- **Asynchronous Operations**: Non-blocking downloads, installations, and AI computations
- **Dynamic Path Handling**: No hardcoded paths; all paths constructed at runtime
- **Interprocess Communication**: Standardized JSON communication between Blender and isolated engines

## Technical Approach

### Separation of Concerns
The architecture strictly separates Blender-specific code (based on bpy) from standard Python logic. The network, extraction, and isolated worker code have no dependencies on Blender's internal libraries.

### Asynchronous Execution
All heavy operations including downloads, installations, and AI computations are executed asynchronously to prevent blocking Blender's main thread. Threading and modal operators (`bpy.types.Operator` with timers) are used for UI updates.

### Environmental Isolation
All pip package installations are scoped to the microservice folder using subprocess to invoke isolated Python executables with concatenated library lists for optimized dependency resolution.

### Dynamic Path Management
No absolute paths are hardcoded in code or JSON files. All paths are constructed at runtime based on the actual addon location on the user's computer.

### Interprocess Communication
Parameter and result passing between Blender and the isolated engine occurs through standardized JSON strings using `sys.argv`, temporary files, or reading standard output via subprocess.Popen with advanced exception handling and timeout management for external engine crashes.

## Installation Process

1. **Configuration Reading**: The system reads `service_config.json` to determine required Python runtime version and dependencies
2. **Manifest Retrieval**: Downloads `exa_manifest.json` from the remote repository to get platform-specific download URLs
3. **Runtime Download**: Downloads the appropriate Python runtime for the user's platform
4. **Dependency Installation**: Installs specified packages using pip in the isolated environment
5. **Asset Acquisition**: Downloads required AI models and assets
6. **Environment Setup**: Configures the isolated Python environment with all dependencies

## Usage

### For Add-on Developers
- Integrate ExaCoreAi as a dependency for advanced AI-powered Blender add-ons
- Use the provided installer interface to manage microservice installations
- Implement custom workers that communicate with Blender through JSON-based protocols

### For End Users
1. Install the Blender add-on
2. Run the installation operator from the add-on preferences
3. The system will download and install all required components in an isolated environment
4. Use the AI-powered features without affecting Blender's performance or stability

## Security Considerations

- All downloaded files are verified using SHA256 checksums
- Isolated environments prevent any interference with Blender's Python environment
- Temporary files are properly managed and cleaned up after operations

## System Requirements

- Blender 3.0 or higher
- Internet connection for downloading runtime components
- Sufficient disk space for Python runtime and AI models (typically 500MB+ depending on requirements)

## License

This project is licensed under the GNU General Public License v3.0 - see the LICENSE file for details.

## Author

Andrea Donati
