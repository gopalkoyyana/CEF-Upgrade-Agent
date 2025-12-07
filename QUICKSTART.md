# CEF Upgrade Agent - Quick Start Guide

This guide will help you get started with the CEF Upgrade Agent quickly.

## Installation

1. **Install Python 3.6+** if not already installed

2. **Download the agent**:
   ```bash
   git clone https://github.com/yourusername/CEF-Upgrade-Agent.git
   cd CEF-Upgrade-Agent
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Basic Workflow

### Step 1: Find Your CEF Version

First, determine what CEF version you want to install. Visit:
- [CEF Builds Index](https://cef-builds.spotifycdn.com/index.html)

Choose a version based on:
- **Chromium version** you need
- **Platform** (Windows, macOS, Linux)
- **Architecture** (x64, x86, ARM64)
- **Build type** (Standard or Minimal)

Example version: `120.1.10+g3ce3184+chromium-120.0.6099.129`

### Step 2: Run a Dry Run

**Always start with a dry run** to see what will happen:

```bash
python cef_upgrade_agent.py --target-version "120.1.10+g3ce3184+chromium-120.0.6099.129" --dry-run
```

This will:
- ✓ Check for vulnerabilities
- ✓ Detect existing CEF installations
- ✓ Show what would be downloaded
- ✓ Show where files would be installed
- ✗ NOT make any actual changes

### Step 3: Review the Output

The dry run will show you:

```
======================================================================
SECURITY CHECK: Vulnerability Scan
======================================================================
✓ No known vulnerabilities found for CEF 120.1.10+g3ce3184+chromium-120.0.6099.129

======================================================================
CEF Detection
======================================================================
✗ No CEF installation detected

======================================================================
Downloading CEF
======================================================================
[DRY RUN] Would download to: temp/cef-downloads/cef_binary_...

======================================================================
Installing CEF
======================================================================
[DRY RUN] Would install from ... to ./cef_installation
```

### Step 4: Run the Actual Upgrade

If everything looks good, run without `--dry-run`:

```bash
python cef_upgrade_agent.py --target-version "120.1.10+g3ce3184+chromium-120.0.6099.129"
```

### Step 5: Review the Report

After completion, check the generated report:

```bash
# Location will be shown in output, typically:
cat temp/cef-agent-logs/YYYYMMDD_HHMMSS/README.md
```

## Common Use Cases

### Use Case 1: Install CEF for Development

```bash
# Install to a specific directory for your project
python cef_upgrade_agent.py \
  --target-version "120.1.10+g3ce3184+chromium-120.0.6099.129" \
  --install-dir "C:\MyProject\cef"
```

### Use Case 2: Upgrade CEF in an Existing Application

```bash
# Detect and upgrade CEF in an application
python cef_upgrade_agent.py \
  --target-version "120.1.10+g3ce3184+chromium-120.0.6099.129" \
  --app-path "C:\Program Files\MyApp"
```

This will:
1. Detect the current CEF version in MyApp
2. Create a backup
3. Download the new version
4. Install it to the detected location

### Use Case 3: Test Multiple Versions

```bash
# Test different versions with dry runs
python cef_upgrade_agent.py --target-version "120.1.10+g3ce3184+chromium-120.0.6099.129" --dry-run
python cef_upgrade_agent.py --target-version "119.4.7+g55e15c8+chromium-119.0.6045.199" --dry-run
python cef_upgrade_agent.py --target-version "118.7.1+g99817d2+chromium-118.0.5993.119" --dry-run
```

## Platform-Specific Examples

### Windows

```powershell
# Install CEF for a Windows application
python cef_upgrade_agent.py `
  --target-version "120.1.10+g3ce3184+chromium-120.0.6099.129" `
  --install-dir "C:\CEF" `
  --backup-dir "D:\Backups\CEF" `
  --log-dir "D:\Logs\CEF"
```

### macOS

```bash
# Install CEF for a macOS application
python3 cef_upgrade_agent.py \
  --target-version "120.1.10+g3ce3184+chromium-120.0.6099.129" \
  --install-dir "/Applications/MyApp.app/Contents/Frameworks" \
  --backup-dir "~/Backups/CEF" \
  --log-dir "~/Logs/CEF"
```

### Linux

```bash
# Install CEF for a Linux application
python3 cef_upgrade_agent.py \
  --target-version "120.1.10+g3ce3184+chromium-120.0.6099.129" \
  --install-dir "/opt/myapp/cef" \
  --backup-dir "/var/backups/cef" \
  --log-dir "/var/log/cef-agent"
```

## Understanding the Output

### Vulnerability Check

```
✓ No known vulnerabilities found
```
✅ Safe to proceed

```
⚠ WARNING: 2 vulnerabilities found
  MEDIUM: 2
```
⚠️ Proceed with caution

```
❌ ABORTING: Critical or high severity vulnerabilities detected!
```
🛑 Choose a different version

### Detection

```
✓ CEF Found!
  Version: 119.4.7
  Chromium Version: 119.0.6045.199
```
ℹ️ Existing installation detected, will be backed up

```
✗ No CEF installation detected
```
ℹ️ Fresh installation

### Download

```
✓ Download complete: temp/cef-downloads/cef_binary_...
  Size: 234.56 MB
```
✅ Download successful

### Installation

```
✓ CEF installed successfully
```
✅ Installation complete

### Verification

```
✓ Installation verified successfully
  Checks: 3/3 passed
```
✅ All checks passed

## Troubleshooting Quick Fixes

### Problem: "requests library not found"

**Solution**:
```bash
pip install requests
```

### Problem: "Could not determine download URL"

**Solution**:
1. Check your version string is correct
2. Visit https://cef-builds.spotifycdn.com/index.html
3. Copy the exact version string from there

### Problem: "Download failed"

**Solution**:
1. Check your internet connection
2. Try again (downloads can be flaky)
3. Try a different CEF version

### Problem: "Verification failed"

**Solution**:
1. Check the installation directory manually
2. Look for libcef.dll/so/dylib
3. Check the detailed logs in commands.log

### Problem: "Permission denied"

**Solution**:
- **Windows**: Run as Administrator
- **macOS/Linux**: Use `sudo` or change installation directory

## Next Steps

After successful installation:

1. **Test your application** with the new CEF version
2. **Check application logs** for any errors
3. **Monitor performance** and stability
4. **Keep the backup** until you're confident
5. **Document** which CEF version you're using

## Getting Help

If you encounter issues:

1. Check the full README.md
2. Review the generated report in logs
3. Check the commands.log for detailed output
4. Open an issue on GitHub with:
   - Your OS and Python version
   - The exact command you ran
   - The full error message
   - The relevant logs

## Best Practices

✅ **DO**:
- Always run a dry run first
- Review vulnerability reports
- Keep backups
- Test in non-production first
- Document your CEF version

❌ **DON'T**:
- Skip the dry run
- Ignore vulnerability warnings
- Delete backups immediately
- Upgrade production without testing
- Use random CEF versions

## Quick Reference

```bash
# Dry run
python cef_upgrade_agent.py --target-version "VERSION" --dry-run

# Install to default location
python cef_upgrade_agent.py --target-version "VERSION"

# Install to custom location
python cef_upgrade_agent.py --target-version "VERSION" --install-dir "PATH"

# Upgrade existing app
python cef_upgrade_agent.py --target-version "VERSION" --app-path "PATH"

# Full custom command
python cef_upgrade_agent.py \
  --target-version "VERSION" \
  --install-dir "INSTALL_PATH" \
  --backup-dir "BACKUP_PATH" \
  --log-dir "LOG_PATH"
```

---

**Ready to start?** Run your first dry run now! 🚀
