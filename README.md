# CEF Upgrade Agent

> **🚀 New to this project?** Read **[START_HERE.md](START_HERE.md)** for a quick guide on which files to read!

A comprehensive Python toolkit for automating CEF (Chromium Embedded Framework) download, build, and deployment.

## Quick Start

### 1. Edit Configuration

Edit `cef_config.json`:

```json
{
  "cef_version": "140.1.13+g5eb3258+chromium-140.0.7339.41",
  "output_directory": "bin/NT/cef/release"
}
```

### 2. Run the Agent

```bash
python cef_unified_agent.py
```

That's it! The agent will:
- ✅ Download CEF binaries
- ✅ Build libcef_dll_wrapper
- ✅ Deploy everything to your output directory

## Features

- **Single Command Workflow**: Complete download and build automation
- **Configuration File**: All settings in `cef_config.json` - no hardcoded versions
- **Automated Build**: Downloads CMake, configures Visual Studio, builds wrapper
- **Security First**: Vulnerability scanning via OSV.dev API
- **Cross-Platform**: Windows, macOS, and Linux support
- **Dry-Run Mode**: Test without making changes
- **MFC Integration**: Optional automatic MFC GUI solution building and deployment

## What is CEF?

The Chromium Embedded Framework (CEF) is an open-source framework for embedding Chromium-based browsers in applications. Used by Spotify, Discord, Visual Studio Code, Steam, and many more.

## Prerequisites

- **Python 3.6+**
- **Visual Studio** (2015, 2017, 2019, or 2022) with C++ tools
- **Internet connection** (for downloads)

## Installation

```bash
git clone https://github.com/gopalkoyyana/CEF-Upgrade-Agent.git
cd CEF-Upgrade-Agent
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python cef_unified_agent.py
```

### Dry Run (Recommended First)

```bash
python cef_unified_agent.py --dry-run
```

### Show Configuration

```bash
python cef_unified_agent.py --show-config
```

### Custom Configuration

```bash
python cef_unified_agent.py --config my_project.json
```

## MFC Integration

To enable automatic MFC GUI integration, add to `cef_config.json`:

```json
{
  "enable_mfc_integration": true,
  "mfc_solution_path": "C:/YourProject/YourApp.sln",
  "mfc_binary_dir": "C:/YourProject/bin/Release",
  "mfc_cef_binary_dir": "C:/YourProject/bin/NT/cef/release/x64"
}
```

The agent will automatically:
1. Build your MFC solution
2. Deploy CEF binaries to MFC directories
3. Generate testing instructions

## Documentation

- **[GUIDE.md](GUIDE.md)** - Complete usage guide (start here!)
- **[CHANGELOG.md](CHANGELOG.md)** - Version history
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines

## Output Structure

After successful build:

```
bin/NT/cef/release/
├── include/                    # CEF header files
├── libcef.dll                  # Main CEF library
├── libcef_dll_wrapper.lib      # Compiled wrapper library
├── *.pak files                 # Resources
├── locales/                    # Locale files
└── ...                         # Other runtime files
```

## Advanced Usage

### Individual Agents

For granular control:

```bash
# Download only
python cef_upgrade_agent.py --target-version "VERSION" --install-dir "DIR"

# Build only
python cef_build_agent.py --cef-source "DIR" --output-dir "OUTPUT"
```

## Troubleshooting

See [GUIDE.md](GUIDE.md) for detailed troubleshooting steps.

Common issues:
- **Visual Studio not found**: Install VS with C++ tools
- **Build failed**: Check logs in `temp/cef-unified-logs/`
- **MFC integration issues**: Verify paths in config

## Security

Automatic vulnerability checking via OSV.dev API:
- Checks before any download
- Aborts on critical/high severity issues
- Displays detailed vulnerability information

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: [GUIDE.md](GUIDE.md)
- **Issues**: [GitHub Issues](https://github.com/gopalkoyyana/CEF-Upgrade-Agent/issues)
- **CEF Official**: https://bitbucket.org/chromiumembedded/cef

## Acknowledgments

- CEF Project: https://bitbucket.org/chromiumembedded/cef
- Chromium Project: https://www.chromium.org/
- OSV.dev: https://osv.dev
- Spotify CDN for hosting CEF builds

---

**Version**: 2.0.0  
**Last Updated**: 2025-12-25  
**Status**: Production Ready

Built with ❤️ for the developer community
