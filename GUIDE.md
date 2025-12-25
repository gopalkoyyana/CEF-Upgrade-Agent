# CEF Upgrade Agent - Complete Guide

## Table of Contents

1. [Quick Start](#quick-start)
2. [Configuration](#configuration)
3. [Usage Examples](#usage-examples)
4. [MFC Integration](#mfc-integration)
5. [Advanced Usage](#advanced-usage)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure

Edit `cef_config.json`:

```json
{
  "cef_version": "140.1.13+g5eb3258+chromium-140.0.7339.41",
  "output_directory": "bin/NT/cef/release"
}
```

### 3. Run

```bash
python cef_unified_agent.py
```

That's it! The agent will download CEF, build libcef_dll_wrapper, and deploy everything.

---

## Configuration

### Configuration File: `cef_config.json`

```json
{
  "cef_version": "140.1.13+g5eb3258+chromium-140.0.7339.41",
  "platform": "windows64",
  "architecture": "x64",
  "build_configuration": "Release",
  "cmake_version": "3.30.1",
  "vs_generator": "Visual Studio 17 2022",
  "output_directory": "bin/NT/cef/release",
  "temp_directory": "temp/cef-workflow",
  "runtime_library": "MultiThreadedDLL",
  
  "_comment": "MFC Integration (optional)",
  "enable_mfc_integration": false,
  "mfc_solution_path": "",
  "mfc_binary_dir": "",
  "mfc_cef_binary_dir": ""
}
```

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `cef_version` | CEF version to download/build | Required |
| `platform` | Target platform | `"windows64"` |
| `architecture` | Build architecture | `"x64"` |
| `build_configuration` | Build type | `"Release"` |
| `cmake_version` | CMake version | `"3.30.1"` |
| `vs_generator` | Visual Studio version | `"Visual Studio 17 2022"` |
| `output_directory` | Final output location | `"bin/NT/cef/release"` |
| `temp_directory` | Temporary files | `"temp/cef-workflow"` |
| `runtime_library` | Runtime library type | `"MultiThreadedDLL"` |

### Finding CEF Versions

1. Visit: https://cef-builds.spotifycdn.com/index.html
2. Select your platform
3. Choose Chromium version
4. Copy the full version string
5. Update `cef_version` in config

---

## Usage Examples

### Basic Usage

```bash
# Use default config
python cef_unified_agent.py
```

### Dry Run (Recommended First)

```bash
# Preview without making changes
python cef_unified_agent.py --dry-run
```

### Show Configuration

```bash
# Display current settings
python cef_unified_agent.py --show-config
```

### Custom Configuration

```bash
# Use different config file
python cef_unified_agent.py --config my_project.json
```

### Partial Workflows

```bash
# Only download CEF
python cef_unified_agent.py --skip-build

# Only build (use existing CEF)
python cef_unified_agent.py --skip-download
```

---

## MFC Integration

### Enable MFC Integration

Add to `cef_config.json`:

```json
{
  "enable_mfc_integration": true,
  "mfc_solution_path": "C:/YourProject/YourApp.sln",
  "mfc_binary_dir": "C:/YourProject/bin/Release",
  "mfc_cef_binary_dir": "C:/YourProject/bin/NT/cef/release/x64"
}
```

### What It Does

When enabled, the agent will:

1. ✅ Download and build CEF (Phase 1 & 2)
2. ✅ Build your MFC GUI solution (Phase 3)
3. ✅ Deploy CEF binaries to MFC directories
4. ✅ Generate `MFC_TEST_INSTRUCTIONS.md`

### Binary Deployment

**Location 1**: `bin/NT/cef/release`
- Complete CEF distribution
- Headers, libraries, resources

**Location 2**: `mfc_cef_binary_dir` (e.g., `bin/NT/cef/release/x64`)
- Complete CEF distribution for MFC
- Used by your application

**Location 3**: `mfc_binary_dir` (MFC executable directory)
- Runtime DLLs only
- libcef.dll, chrome_elf.dll, etc.
- Resources and locales

### Testing Your MFC Application

After completion, check `MFC_TEST_INSTRUCTIONS.md` for:
- Verification checklist
- Launch instructions
- Test cases for Home context
- Troubleshooting steps

---

## Advanced Usage

### Using Individual Agents

For granular control, use individual agents:

#### Download Only

```bash
python cef_upgrade_agent.py \
  --target-version "140.1.13+g5eb3258+chromium-140.0.7339.41" \
  --install-dir "C:\cef_binary"
```

#### Build Only

```bash
python cef_build_agent.py \
  --cef-source "C:\cef_binary" \
  --output-dir "bin/NT/cef/release"
```

### Multiple Projects

Use different configs:

```bash
# Project A
python cef_unified_agent.py --config project_a.json

# Project B
python cef_unified_agent.py --config project_b.json
```

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Build CEF
  run: |
    python cef_unified_agent.py --config .github/cef_config.json
```

---

## Troubleshooting

### Visual Studio Not Found

**Solution**: Install Visual Studio with "Desktop development with C++" workload.

### CMake Download Failed

**Solution**: Use existing CMake:
```bash
python cef_build_agent.py --cmake-path "C:\Program Files\CMake\bin\cmake.exe"
```

### Build Failed

**Solutions**:
1. Check logs in `temp/cef-unified-logs/`
2. Ensure Visual Studio is installed
3. Try different CEF version
4. Run with `--dry-run` first

### MFC Solution Won't Build

**Solutions**:
1. Verify `mfc_solution_path` is correct
2. Ensure solution builds manually
3. Check Visual Studio installation
4. Review build logs

### Binaries Not Deployed

**Solutions**:
1. Check `mfc_binary_dir` path
2. Verify directory permissions
3. Ensure directories exist
4. Check deployment logs

### Application Won't Start

**Solutions**:
1. Verify all CEF DLLs present
2. Check `locales/` directory exists
3. Ensure *.pak files present
4. Verify correct architecture (x64)

---

## Workflow

### Complete Workflow (3 Phases)

```
Phase 1: Download CEF
├── Vulnerability check (OSV.dev)
├── Download binaries
├── Extract archive
└── Install to temp directory

Phase 2: Build libcef_dll_wrapper
├── Download CMake (if needed)
├── Configure with Visual Studio
├── Modify project properties (/MD)
├── Build wrapper library
└── Deploy to output directory

Phase 3: MFC Integration (optional)
├── Build MFC solution
├── Deploy to mfc_cef_binary_dir
├── Deploy runtime to mfc_binary_dir
└── Generate test instructions
```

### Output Structure

```
bin/NT/cef/release/
├── include/                    # CEF headers
├── libcef.dll                  # Main library
├── libcef_dll_wrapper.lib      # Wrapper library
├── chrome_elf.dll
├── *.pak files                 # Resources
├── locales/                    # Locale files
└── ...
```

---

## Command Reference

```bash
# Show configuration
python cef_unified_agent.py --show-config

# Dry run
python cef_unified_agent.py --dry-run

# Full run
python cef_unified_agent.py

# Custom config
python cef_unified_agent.py --config custom.json

# Skip download
python cef_unified_agent.py --skip-download

# Skip build
python cef_unified_agent.py --skip-build

# Individual agents
python cef_upgrade_agent.py --target-version "VERSION" --install-dir "DIR"
python cef_build_agent.py --cef-source "DIR" --output-dir "OUTPUT"
```

---

## Best Practices

1. ✅ **Always dry-run first**
   ```bash
   python cef_unified_agent.py --dry-run
   ```

2. ✅ **Version control your config**
   - Commit `cef_config.json` to git
   - Track CEF version changes

3. ✅ **Test thoroughly**
   - Follow test instructions
   - Test all major features
   - Check performance

4. ✅ **Keep backups**
   - Agent creates automatic backups
   - Keep until testing complete

5. ✅ **Document your setup**
   - Note which CEF version works
   - Document custom configurations

---

## Security

The agent automatically checks for vulnerabilities using OSV.dev API:
- Queries before any download
- Aborts on critical/high severity
- Displays vulnerability details
- Cannot be bypassed

---

## Support

- **Documentation**: This guide
- **Issues**: GitHub Issues
- **CEF Official**: https://bitbucket.org/chromiumembedded/cef
- **Builds**: https://cef-builds.spotifycdn.com/

---

## Summary

### What You Get

- ✅ **Single command** for complete workflow
- ✅ **No hardcoded versions** - all in config
- ✅ **Automated building** - CMake + MSBuild
- ✅ **MFC integration** - optional automatic deployment
- ✅ **Security first** - vulnerability scanning
- ✅ **Well tested** - comprehensive test suite

### Quick Start Recap

1. Edit `cef_config.json`
2. Run `python cef_unified_agent.py`
3. Done!

**Everything you need in one place!** 🚀
