# ExaAiCore

ExaAiCore is a modular architecture designed to deploy and manage isolated Python environments called microservices for Blender addons, such as HDRi Maker. The primary goal is to run heavy AI frameworks like PyTorch and Diffusers in a completely separate process, preventing dependency conflicts with Blender's native Python interpreter and avoiding UI blocking or crashes.

## Architecture

The system consists of three main components:

1. **Remote Repository**: A GitHub repository hosting ZIP files containing standalone Python engines for Windows, macOS, and Linux, along with an `exa_manifest.json` file that maps direct download URLs.
2. **Local Bootstrapper**: A folder `exa_service_builder` integrated into the Blender addon. It contains:
   - `service_config.json`: Configuration file
   - `installer.py`: Pure Python script for network logic and extraction
   - `installer_ops.py`: Blender interface for user interaction
3. **Microservice Worker**: A Python script that runs within the isolated environment, loading AI models, processing data, and returning results to Blender.

## Key Features

- **Separation of Concerns**: Clear distinction between Blender-specific code and standard Python logic. Network code, extraction logic, and isolated workers have no dependencies on internal Blender libraries.
- **Asynchronous Execution**: Heavy operations like downloads, installations, or AI computations never block Blender's main thread. Uses threading and modal bpy operators with timers for UI updates.
- **Environmental Isolation**: All package installations via pip are scoped to the microservice folder. Uses the subprocess module to invoke isolated Python executables, passing concatenated library lists in a single command for optimized dependency resolution.
- **Dynamic Path Management**: Never hardcodes absolute paths in code or JSON files. Always uses `os.path` to construct paths at runtime based on the actual addon location on the user's computer.
- **Interprocess Communication**: Parameter and result passing between Blender and the isolated engine occurs via standardized JSON strings. Uses `sys.argv`, temporary files, or reading standard output through `subprocess.Popen`, including advanced exception handling and timeout management for external engine crashes.

## Project Structure

```
exa_service_builder/
├── __init__.py
├── bl_ops_installer.py        # Blender operator for installation
├── config_reader.py             # Reads configuration and generates universal installation plans
├── downloader.py              # Handles resource downloads with integrity checking
├── exa_manifest.json          # Remote manifest mapping download URLs
├── extractor.py                 # Extracts archives and normalizes directory structures
├── orchestrator.py              # Coordinates background pipeline and communication
├── package_manager.py             # Manages dependency installations for runtimes
└── platform_detector.py           # Detects system platform and architecture
```

## Configuration

The `service_config.json` file defines:
- Runtime environments (Python versions, dependencies)
- Assets to download
- Remote manifest URL
- Target folder name

The `exa_manifest.json` file contains platform-specific download URLs for runtimes and assets with SHA256 checksums.

## Installation Process

1. User initiates installation through Blender UI
2. Configuration is read from `service_config.json`
3. Remote manifest is fetched from the specified URL
4. Platform-specific resources are identified
5. Resources are downloaded with integrity verification
6. Archives are extracted and normalized
7. Dependencies are installed in isolated environments

## Development Guidelines

- Use relative imports (.) for internal modules
- All code should be clean, modular, and production-ready
- Prefer standard Python libraries over external dependencies
- Implement proper error handling with try/except blocks where necessary
- Follow PEP 257 docstring conventions in English
- Never hardcode absolute paths; always use dynamic path construction

## License

This project is licensed under the GNU General Public License v3.0 - see the LICENSE file for details.
