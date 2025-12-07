# CEF Upgrade Agent

A cross-platform Python agent designed to detect, backup, and upgrade CEF (Chromium Embedded Framework) installations on Windows, macOS, and Linux.

## Features

*   **Vulnerability Check**: Automatically checks for known vulnerabilities in the target CEF version using the OSV.dev API before any download or upgrade. Aborts if critical or high severity vulnerabilities are detected.
*   **Detection**: Identifies existing CEF installations in applications or system-wide.
*   **Backup**: Automatically backs up existing CEF binaries and resources before making changes.
*   **Smart Download**: Downloads official CEF binary distributions from the Spotify CDN.
*   **Installation**: Extracts and installs CEF to specified directories.
*   **Verification**: Validates installation by checking for required libraries, resources, and locales.
*   **Reporting**: Generates detailed logs and a comprehensive run report.

## What is CEF?

The Chromium Embedded Framework (CEF) is an open-source framework for embedding a Chromium-based web browser in other applications. It's used by many popular applications including:

- Spotify Desktop
- Discord
- Visual Studio Code (Electron apps)
- Steam Client
- Adobe Creative Cloud
- And many more...

## Prerequisites

*   **Python 3.6+** installed on the system.
*   **Internet Access**: Required to download CEF binaries and check for vulnerabilities.
*   **Sufficient Disk Space**: CEF distributions can be 100-500 MB depending on the version and platform.

## Installation

1. Clone or download this repository:

```bash
git clone https://github.com/yourusername/CEF-Upgrade-Agent.git
cd CEF-Upgrade-Agent
```

2. Install required dependencies:

```bash
pip install -r requirements.txt
```

Or install the requests library directly:

```bash
pip install requests
```

**Note**: The `requests` library is required for downloading CEF binaries and vulnerability checking. If not installed, the agent will not function properly.

## Usage

Run the script from the command line using Python 3.

### Basic Usage

To download and install a specific CEF version:

```bash
python cef_upgrade_agent.py --target-version "120.1.10+g3ce3184+chromium-120.0.6099.129"
```

### Dry Run (Recommended First Step)

To see what the agent *would* do without actually making any changes:

```bash
python cef_upgrade_agent.py --target-version "120.1.10+g3ce3184+chromium-120.0.6099.129" --dry-run
```

### Upgrading CEF in a Specific Application

To detect and upgrade CEF in a specific application:

```bash
python cef_upgrade_agent.py --target-version "120.1.10+g3ce3184+chromium-120.0.6099.129" --app-path "C:\Program Files\MyApp"
```

### Custom Installation Directory

To install CEF to a specific directory:

```bash
python cef_upgrade_agent.py --target-version "120.1.10+g3ce3184+chromium-120.0.6099.129" --install-dir "C:\CEF"
```

### Customizing Backup and Log Directories

You can specify where backups and logs are stored:

```bash
python cef_upgrade_agent.py \
  --target-version "120.1.10+g3ce3184+chromium-120.0.6099.129" \
  --backup-dir "D:\Backups\CEF" \
  --log-dir "D:\Logs\CEF-Agent"
```

## Finding CEF Versions

CEF versions follow a specific format: `{CEF_VERSION}+{COMMIT}+chromium-{CHROMIUM_VERSION}`

To find available versions:

1. Visit the [CEF Builds Index](https://cef-builds.spotifycdn.com/index.html)
2. Choose your platform (Windows, macOS, Linux)
3. Select the Chromium version you need
4. Copy the full version string

Example version strings:
- `120.1.10+g3ce3184+chromium-120.0.6099.129` (Chromium 120)
- `119.4.7+g55e15c8+chromium-119.0.6045.199` (Chromium 119)
- `118.7.1+g99817d2+chromium-118.0.5993.119` (Chromium 118)

## Vulnerability Check

**Important Security Feature**: Before any download or upgrade operation (including dry-runs), the agent automatically checks for known vulnerabilities in the specified CEF/Chromium version using the [OSV.dev](https://osv.dev) vulnerability database.

### How It Works

1. The agent queries the OSV.dev API for the target CEF/Chromium version
2. If vulnerabilities are found, they are displayed with severity levels
3. **Critical or High severity vulnerabilities will abort the operation**
4. Medium or Low severity vulnerabilities will display a warning but allow you to proceed

### Example Output

```
======================================================================
SECURITY CHECK: Vulnerability Scan
======================================================================

Checking for vulnerabilities in CEF 120.1.10+g3ce3184+chromium-120.0.6099.129...

======================================================================
⚠ WARNING: 3 vulnerabilities found for CEF 120.1.10+g3ce3184+chromium-120.0.6099.129
======================================================================
  CRITICAL: 1
  HIGH: 1
  MEDIUM: 1

Vulnerability Details:
----------------------------------------------------------------------

  ID: CVE-2024-XXXXX
  Severity: CRITICAL
  Summary: Use-after-free in WebRTC...
  Details: https://osv.dev/vulnerability/CVE-2024-XXXXX

❌ ABORTING: Critical or high severity vulnerabilities detected!
   Found 1 CRITICAL and 1 HIGH severity issues.

   Recommendation: Choose a different CEF version without known vulnerabilities.
   Visit https://bitbucket.org/chromiumembedded/cef/wiki/Home for more information.
```

### Bypassing the Check

The vulnerability check **cannot be bypassed**. This is a critical security feature designed to prevent you from installing vulnerable versions of CEF. If you need to proceed with a version that has known vulnerabilities, you must modify the source code (not recommended for production use).

## Command Line Arguments

| Argument | Description | Required | Default |
| :--- | :--- | :--- | :--- |
| `--target-version` | The CEF version to install (e.g., `120.1.10+g3ce3184+chromium-120.0.6099.129`). | **Yes** | - |
| `--app-path` | Path to an application directory to detect existing CEF installation. | No | `None` |
| `--install-dir` | Directory to install CEF. | No | `./cef_installation` |
| `--dry-run` | Simulate the process without making changes. | No | `False` |
| `--backup-dir` | Directory to store backups. | No | `temp/cef-agent-backups` |
| `--log-dir` | Directory to store logs and reports. | No | `temp/cef-agent-logs` |

## Output

The agent creates a timestamped directory in the `log-dir` containing:

*   **`README.md`**: A comprehensive summary report of the run including:
    - Detection results
    - Vulnerability check results
    - Backup information
    - Download details
    - Installation status
    - Verification results
    - Rollback instructions
    - Next steps

*   **`commands.log`**: A detailed log of all operations and their output.

*   **`agent-run.jsonl`**: Structured logs in JSONL format for programmatic analysis.

## Rollback

If an upgrade causes issues, the agent provides rollback instructions in the generated run report (`README.md` in the log directory). Generally, this involves:

1. Stop any applications using CEF
2. Restore the files from the created backup tarball:
   ```bash
   tar -xzf temp/cef-agent-backups/cef_backup_TIMESTAMP.tar.gz -C /path/to/restore
   ```
3. Restart your applications

## Platform-Specific Notes

### Windows

- CEF files include: `libcef.dll`, `chrome_elf.dll`, various `.pak` files
- Typical installation locations: `C:\Program Files\`, `C:\Program Files (x86)\`
- May require administrator privileges for system-wide installations

### macOS

- CEF is typically packaged as `Chromium Embedded Framework.framework`
- Common locations: `/Applications/`, `~/Applications/`, `/Library/Frameworks/`
- May need to grant permissions for downloaded binaries

### Linux

- CEF files include: `libcef.so`, various `.pak` files
- Common locations: `/opt/`, `/usr/local/`, `~/.local/`
- Ensure proper file permissions after installation

## Troubleshooting

### Download Fails

If the download fails:
1. Check your internet connection
2. Verify the version string is correct
3. Try a different CEF version
4. Check the [CEF Builds Index](https://cef-builds.spotifycdn.com/index.html) for available versions

### Installation Verification Fails

If verification fails but files were extracted:
1. Check the installation directory manually
2. Ensure all required files are present (libcef, .pak files, locales)
3. Check file permissions
4. Review the detailed logs in `commands.log`

### Application Won't Start After Upgrade

If your application fails to start after upgrading CEF:
1. Check version compatibility with your application
2. Restore from backup immediately
3. Review application logs for specific errors
4. Consider using a different CEF version closer to the original

## CEF Version Compatibility

**Important**: Not all CEF versions are compatible with all applications. Consider:

- **API Changes**: Major CEF versions may have breaking API changes
- **Chromium Version**: Ensure the Chromium version is compatible with your needs
- **Platform Support**: Some versions may not support older operating systems
- **Application Requirements**: Check your application's documentation for supported CEF versions

## Security Best Practices

1. **Always run a dry-run first** to understand what changes will be made
2. **Review vulnerability reports** before proceeding with any installation
3. **Keep backups** of working CEF installations
4. **Test thoroughly** after any upgrade
5. **Monitor security advisories** for CEF and Chromium
6. **Use the latest stable version** when possible

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- CEF Project: https://bitbucket.org/chromiumembedded/cef
- Chromium Project: https://www.chromium.org/
- OSV.dev for vulnerability data: https://osv.dev
- Spotify CDN for hosting CEF builds

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review the troubleshooting section above

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and changes.
