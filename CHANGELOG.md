# Changelog

All notable changes to the CEF Upgrade Agent project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-12-25

### Added - CEF Unified Agent (RECOMMENDED)

- **NEW: Unified Agent** (`cef_unified_agent.py`)
  - Single command for complete download + build workflow
  - Configuration file support (`cef_config.json`)
  - No hardcoded versions - all settings externalized
  - Integrated logging for both phases
  - Phase control (skip download or build)
  - Custom config file support
  - Display configuration option

- **Configuration Management**
  - JSON-based configuration file
  - Auto-creation of default config
  - Support for multiple config files
  - Version control friendly
  - Easy version updates

- **ConfigManager Class**
  - Load/save configuration from JSON
  - Merge with default settings
  - Validation and error handling
  - Display current configuration

### Added - CEF Build Agent

- **NEW: Complete Build Automation** (`cef_build_agent.py`)
  - Automated CMake download and configuration
  - Visual Studio project generation and configuration
  - Automatic Runtime Library modification (/MD)
  - MSBuild integration for libcef_dll_wrapper compilation
  - Binary collection from multiple locations (include, Release, Resources, libcef_dll_wrapper.lib)
  - Deployment to customizable target directory
  - Support for Visual Studio 2015-2022
  - Dry-run mode for safe testing

- **CMakeDownloader Class**
  - Automatic CMake binary download from GitHub releases
  - Cross-platform support (Windows, macOS, Linux)
  - Version-specific downloads
  - Archive extraction

- **CMakeConfigurator Class**
  - Automated CMake configuration with Visual Studio generators
  - Auto-detection of installed Visual Studio versions
  - Platform architecture selection (x64, Win32)
  - Build directory management

- **VSProjectModifier Class**
  - XML-based .vcxproj file modification
  - Runtime Library setting automation
  - Release configuration targeting

- **VSBuilder Class**
  - MSBuild auto-detection using vswhere
  - Multi-processor build support
  - Target-specific building (libcef_dll_wrapper)
  - Detailed build logging

- **BinaryCollector Class**
  - Multi-source binary collection
  - Structured deployment to target directory
  - Verification of collected files

### Documentation

- Added `BUILD_QUICKSTART.md` - Comprehensive build agent quick start guide
- Updated `README.md` with build agent documentation
- Added build agent usage examples and workflow description
- Created `test_build_agent.py` - Test suite for build automation

### Integration

- Build agent works standalone or with upgrade agent
- Complete workflow: Download CEF → Build wrapper → Deploy binaries
- Unified logging and reporting system

## [1.0.0] - 2025-12-07

### Added
- Initial release of CEF Upgrade Agent
- **Vulnerability Checking**: Integration with OSV.dev API to check for known vulnerabilities
  - Automatic checks before any download or installation
  - Severity-based decision making (abort on CRITICAL/HIGH)
  - Detailed vulnerability reporting
- **CEF Detection**: Automatic detection of existing CEF installations
  - Support for Windows, macOS, and Linux
  - Version extraction from installation files
  - Architecture detection
- **Backup System**: Automatic backup creation before upgrades
  - Compressed tar.gz archives
  - Timestamped backup files
  - Rollback instructions in reports
- **Smart Download**: CEF binary distribution downloads
  - Integration with Spotify CDN (cef-builds.spotifycdn.com)
  - Platform and architecture detection
  - Progress tracking for large downloads
- **Installation Management**: Automated extraction and installation
  - Support for multiple archive formats (.tar.bz2, .zip, .tar.gz)
  - Intelligent CEF directory detection
  - Custom installation directory support
- **Verification System**: Post-installation validation
  - Core library checks (libcef.dll/so/dylib)
  - Resource file validation (.pak files)
  - Locales directory verification
- **Comprehensive Reporting**: Detailed run reports and logs
  - Markdown summary reports
  - Command execution logs
  - JSONL structured logs
  - Rollback instructions
- **Dry Run Mode**: Safe simulation of upgrade process
  - No actual changes made
  - Full process preview
  - Risk assessment
- **Cross-Platform Support**: Works on Windows, macOS, and Linux
  - Platform-specific file detection
  - OS-appropriate paths and commands
  - Architecture awareness

### Features
- Command-line interface with comprehensive options
- Detailed logging at every step
- Error handling and recovery suggestions
- User-friendly output with progress indicators
- Security-first approach with mandatory vulnerability checks

### Documentation
- Comprehensive README with usage examples
- Platform-specific notes and troubleshooting
- Security best practices
- CEF version compatibility guidance
- Rollback procedures

## [Unreleased]

### Planned Features
- Support for custom CEF builds
- Integration with package managers (Chocolatey, Homebrew, APT)
- Automatic version recommendation based on Chromium compatibility
- Health check for applications after upgrade
- Dependency analysis for applications using CEF
- Configuration file support for repeated upgrades
- Batch upgrade support for multiple applications
- Integration with CI/CD pipelines
- Web UI for easier management
- Automatic rollback on verification failure

### Known Issues
- Version detection may not work for heavily customized CEF installations
- Download URLs may change if Spotify CDN structure changes
- Some older CEF versions may not be available for download

### Notes
- This agent is designed for CEF binary distributions, not for building CEF from source
- Always test upgrades in a non-production environment first
- Keep backups of working installations
- Review vulnerability reports carefully before proceeding

---

## Version History

- **1.0.0** (2025-12-07): Initial release with core functionality
