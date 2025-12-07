#!/usr/bin/env python3
"""
CEF (Chromium Embedded Framework) Upgrade Agent

A cross-platform Python agent designed to detect, backup, and upgrade CEF
installations in applications on Windows, macOS, and Linux.

Features:
- Vulnerability checking via OSV.dev API
- Detection of existing CEF installations
- Automatic backup before upgrade
- Smart upgrade with verification
- Detailed reporting and logging
"""

import os
import sys
import argparse
import platform
import subprocess
import shutil
import json
import tarfile
import zipfile
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Optional dependency for vulnerability checking
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("WARNING: 'requests' library not found. Vulnerability checking will be disabled.")
    print("Install with: pip install requests")


class VulnerabilityChecker:
    """Checks for known vulnerabilities in CEF versions using OSV.dev API."""
    
    OSV_API_URL = "https://api.osv.dev/v1/query"
    
    def __init__(self, logger):
        self.logger = logger
        
    def check_version(self, version: str) -> Tuple[bool, List[Dict]]:
        """
        Check if a CEF version has known vulnerabilities.
        
        Returns:
            Tuple of (has_critical_vulns, vulnerabilities_list)
        """
        if not REQUESTS_AVAILABLE:
            self.logger.log("WARNING: Skipping vulnerability check (requests library not available)")
            return False, []
        
        self.logger.log("=" * 70)
        self.logger.log("SECURITY CHECK: Vulnerability Scan")
        self.logger.log("=" * 70)
        self.logger.log(f"\nChecking for vulnerabilities in CEF {version}...\n")
        
        try:
            # Query OSV.dev for CEF vulnerabilities
            # CEF vulnerabilities might be under "chromium" or "cef" ecosystem
            queries = [
                {"package": {"name": "chromium-embedded-framework", "ecosystem": "OSS-Fuzz"}},
                {"package": {"name": "cef", "ecosystem": "OSS-Fuzz"}},
            ]
            
            all_vulnerabilities = []
            
            for query in queries:
                query["version"] = version
                response = requests.post(
                    self.OSV_API_URL,
                    json=query,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "vulns" in data:
                        all_vulnerabilities.extend(data["vulns"])
            
            if not all_vulnerabilities:
                self.logger.log(f"✓ No known vulnerabilities found for CEF {version}")
                self.logger.log("=" * 70 + "\n")
                return False, []
            
            # Analyze severity
            critical_count = 0
            high_count = 0
            medium_count = 0
            low_count = 0
            
            for vuln in all_vulnerabilities:
                severity = self._get_severity(vuln)
                if severity == "CRITICAL":
                    critical_count += 1
                elif severity == "HIGH":
                    high_count += 1
                elif severity == "MEDIUM":
                    medium_count += 1
                else:
                    low_count += 1
            
            # Display results
            self.logger.log("=" * 70)
            self.logger.log(f"⚠ WARNING: {len(all_vulnerabilities)} vulnerabilities found for CEF {version}")
            self.logger.log("=" * 70)
            
            if critical_count > 0:
                self.logger.log(f"  CRITICAL: {critical_count}")
            if high_count > 0:
                self.logger.log(f"  HIGH: {high_count}")
            if medium_count > 0:
                self.logger.log(f"  MEDIUM: {medium_count}")
            if low_count > 0:
                self.logger.log(f"  LOW: {low_count}")
            
            self.logger.log("\nVulnerability Details:")
            self.logger.log("-" * 70)
            
            for vuln in all_vulnerabilities[:5]:  # Show first 5
                vuln_id = vuln.get("id", "Unknown")
                summary = vuln.get("summary", "No summary available")
                severity = self._get_severity(vuln)
                
                self.logger.log(f"\n  ID: {vuln_id}")
                self.logger.log(f"  Severity: {severity}")
                self.logger.log(f"  Summary: {summary[:100]}...")
                self.logger.log(f"  Details: https://osv.dev/vulnerability/{vuln_id}")
            
            if len(all_vulnerabilities) > 5:
                self.logger.log(f"\n  ... and {len(all_vulnerabilities) - 5} more vulnerabilities")
            
            # Determine if we should abort
            has_critical = critical_count > 0 or high_count > 0
            
            if has_critical:
                self.logger.log("\n" + "=" * 70)
                self.logger.log("❌ ABORTING: Critical or high severity vulnerabilities detected!")
                self.logger.log(f"   Found {critical_count} CRITICAL and {high_count} HIGH severity issues.")
                self.logger.log("\n   Recommendation: Choose a different CEF version without known vulnerabilities.")
                self.logger.log("   Visit https://bitbucket.org/chromiumembedded/cef/wiki/Home for more information.")
                self.logger.log("=" * 70 + "\n")
            else:
                self.logger.log("\n" + "=" * 70)
                self.logger.log("⚠ Proceeding with caution: Only medium/low severity vulnerabilities found.")
                self.logger.log("=" * 70 + "\n")
            
            return has_critical, all_vulnerabilities
            
        except requests.exceptions.RequestException as e:
            self.logger.log(f"WARNING: Failed to check vulnerabilities: {e}")
            self.logger.log("Proceeding without vulnerability check...\n")
            return False, []
    
    def _get_severity(self, vuln: Dict) -> str:
        """Extract severity from vulnerability data."""
        if "severity" in vuln:
            if isinstance(vuln["severity"], list) and len(vuln["severity"]) > 0:
                return vuln["severity"][0].get("type", "UNKNOWN").upper()
            elif isinstance(vuln["severity"], str):
                return vuln["severity"].upper()
        
        # Try to infer from CVSS score if available
        if "database_specific" in vuln:
            cvss = vuln["database_specific"].get("cvss_score", 0)
            if cvss >= 9.0:
                return "CRITICAL"
            elif cvss >= 7.0:
                return "HIGH"
            elif cvss >= 4.0:
                return "MEDIUM"
            else:
                return "LOW"
        
        return "UNKNOWN"


class Logger:
    """Handles logging to both console and file."""
    
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.commands_log = log_dir / "commands.log"
        self.jsonl_log = log_dir / "agent-run.jsonl"
        
        # Clear existing logs
        self.commands_log.write_text("")
        self.jsonl_log.write_text("")
    
    def log(self, message: str, level: str = "INFO"):
        """Log a message to console and file."""
        timestamp = datetime.now().isoformat()
        print(message)
        
        # Write to commands.log
        with open(self.commands_log, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
        
        # Write to JSONL
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message
        }
        with open(self.jsonl_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def log_command(self, command: str, output: str = "", returncode: int = 0):
        """Log a command execution."""
        self.log(f"COMMAND: {command}")
        if output:
            self.log(f"OUTPUT:\n{output}")
        self.log(f"RETURN CODE: {returncode}")


class CEFDetector:
    """Detects existing CEF installations."""
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self.os_type = platform.system()
    
    def detect_cef_in_path(self, app_path: Optional[str] = None) -> Dict:
        """
        Detect CEF installation in a specific application path or system-wide.
        
        Returns:
            Dict with detection results including version, paths, and architecture
        """
        self.logger.log("=" * 70)
        self.logger.log("CEF Detection")
        self.logger.log("=" * 70)
        
        result = {
            "found": False,
            "version": None,
            "paths": [],
            "architecture": None,
            "chromium_version": None
        }
        
        if app_path:
            self.logger.log(f"Searching for CEF in: {app_path}")
            result = self._detect_in_directory(Path(app_path))
        else:
            self.logger.log("Searching for CEF installations system-wide...")
            # Search common installation locations
            search_paths = self._get_common_cef_paths()
            for path in search_paths:
                if path.exists():
                    detected = self._detect_in_directory(path)
                    if detected["found"]:
                        result = detected
                        break
        
        if result["found"]:
            self.logger.log(f"\n✓ CEF Found!")
            self.logger.log(f"  Version: {result['version']}")
            self.logger.log(f"  Chromium Version: {result['chromium_version']}")
            self.logger.log(f"  Architecture: {result['architecture']}")
            self.logger.log(f"  Paths: {', '.join(str(p) for p in result['paths'])}")
        else:
            self.logger.log("\n✗ No CEF installation detected")
        
        self.logger.log("=" * 70 + "\n")
        return result
    
    def _detect_in_directory(self, directory: Path) -> Dict:
        """Detect CEF in a specific directory."""
        result = {
            "found": False,
            "version": None,
            "paths": [],
            "architecture": None,
            "chromium_version": None
        }
        
        # Look for CEF-specific files
        cef_indicators = {
            "Windows": ["libcef.dll", "cef.pak", "chrome_elf.dll"],
            "Darwin": ["Chromium Embedded Framework.framework", "libcef.dylib"],
            "Linux": ["libcef.so", "cef.pak"]
        }
        
        indicators = cef_indicators.get(self.os_type, [])
        
        for root, dirs, files in os.walk(directory):
            for indicator in indicators:
                if indicator in files or indicator in dirs:
                    result["found"] = True
                    result["paths"].append(Path(root))
                    
                    # Try to extract version information
                    version_info = self._extract_version_info(Path(root))
                    if version_info:
                        result.update(version_info)
                    
                    break
            
            if result["found"]:
                break
        
        return result
    
    def _extract_version_info(self, cef_path: Path) -> Optional[Dict]:
        """Extract version information from CEF installation."""
        version_info = {}
        
        # Look for version.txt or README.txt
        for version_file in ["version.txt", "README.txt", "VERSION"]:
            version_path = cef_path / version_file
            if version_path.exists():
                try:
                    content = version_path.read_text(encoding="utf-8", errors="ignore")
                    # Parse version information
                    for line in content.split("\n"):
                        if "CEF Version" in line or "cef_version" in line:
                            parts = line.split(":")
                            if len(parts) > 1:
                                version_info["version"] = parts[1].strip()
                        if "Chromium Version" in line or "chromium_version" in line:
                            parts = line.split(":")
                            if len(parts) > 1:
                                version_info["chromium_version"] = parts[1].strip()
                except Exception as e:
                    self.logger.log(f"Warning: Could not read {version_file}: {e}")
        
        # Try to determine architecture
        if self.os_type == "Windows":
            # Check for 32-bit or 64-bit DLLs
            libcef_path = cef_path / "libcef.dll"
            if libcef_path.exists():
                # Simple heuristic: file size
                size_mb = libcef_path.stat().st_size / (1024 * 1024)
                version_info["architecture"] = "x64" if size_mb > 100 else "x86"
        else:
            # For Linux/Mac, use file command or check binary
            version_info["architecture"] = platform.machine()
        
        return version_info if version_info else None
    
    def _get_common_cef_paths(self) -> List[Path]:
        """Get common CEF installation paths based on OS."""
        paths = []
        
        if self.os_type == "Windows":
            paths = [
                Path("C:/Program Files"),
                Path("C:/Program Files (x86)"),
                Path(os.environ.get("LOCALAPPDATA", "")),
                Path(os.environ.get("APPDATA", ""))
            ]
        elif self.os_type == "Darwin":
            paths = [
                Path("/Applications"),
                Path.home() / "Applications",
                Path("/Library/Frameworks"),
                Path.home() / "Library/Frameworks"
            ]
        else:  # Linux
            paths = [
                Path("/opt"),
                Path("/usr/local"),
                Path("/usr/lib"),
                Path.home() / ".local"
            ]
        
        return [p for p in paths if p.exists()]


class CEFBackup:
    """Handles backup of existing CEF installations."""
    
    def __init__(self, logger: Logger, backup_dir: Path):
        self.logger = logger
        self.backup_dir = backup_dir
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, cef_paths: List[Path], dry_run: bool = False) -> Optional[Path]:
        """Create a backup of CEF files."""
        if not cef_paths:
            self.logger.log("No CEF paths to backup")
            return None
        
        self.logger.log("=" * 70)
        self.logger.log("Creating Backup")
        self.logger.log("=" * 70)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"cef_backup_{timestamp}.tar.gz"
        backup_path = self.backup_dir / backup_name
        
        if dry_run:
            self.logger.log(f"[DRY RUN] Would create backup: {backup_path}")
            self.logger.log(f"[DRY RUN] Would backup paths: {', '.join(str(p) for p in cef_paths)}")
            self.logger.log("=" * 70 + "\n")
            return backup_path
        
        try:
            with tarfile.open(backup_path, "w:gz") as tar:
                for path in cef_paths:
                    if path.exists():
                        self.logger.log(f"Backing up: {path}")
                        tar.add(path, arcname=path.name)
            
            size_mb = backup_path.stat().st_size / (1024 * 1024)
            self.logger.log(f"\n✓ Backup created: {backup_path}")
            self.logger.log(f"  Size: {size_mb:.2f} MB")
            self.logger.log("=" * 70 + "\n")
            
            return backup_path
            
        except Exception as e:
            self.logger.log(f"✗ Backup failed: {e}", level="ERROR")
            self.logger.log("=" * 70 + "\n")
            return None


class CEFDownloader:
    """Downloads CEF binaries from official sources."""
    
    CEF_DOWNLOAD_BASE = "https://cef-builds.spotifycdn.com"
    CEF_INDEX_URL = "https://cef-builds.spotifycdn.com/index.json"
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self.os_type = platform.system()
    
    def get_download_url(self, version: str, platform_name: str = None, architecture: str = None) -> Optional[str]:
        """
        Get the download URL for a specific CEF version.
        
        Args:
            version: CEF version (e.g., "120.1.10+g3ce3184+chromium-120.0.6099.129")
            platform_name: Platform (windows, macosx, linux)
            architecture: Architecture (x64, x86, arm64)
        """
        if not REQUESTS_AVAILABLE:
            self.logger.log("ERROR: 'requests' library required for downloading")
            return None
        
        # Determine platform and architecture if not provided
        if not platform_name:
            platform_map = {
                "Windows": "windows",
                "Darwin": "macosx",
                "Linux": "linux"
            }
            platform_name = platform_map.get(self.os_type, "linux")
        
        if not architecture:
            arch_map = {
                "AMD64": "64",
                "x86_64": "64",
                "arm64": "arm64",
                "aarch64": "arm64"
            }
            architecture = arch_map.get(platform.machine(), "64")
        
        self.logger.log(f"Searching for CEF {version} for {platform_name} {architecture}...")
        
        try:
            # Fetch the CEF builds index
            response = requests.get(self.CEF_INDEX_URL, timeout=30)
            response.raise_for_status()
            
            builds = response.json()
            
            # Search for matching build
            for build_type in ["stable", "beta", "dev"]:
                if build_type in builds:
                    for build in builds[build_type]:
                        if version in build.get("cef_version", ""):
                            files = build.get("files", [])
                            for file_info in files:
                                if (platform_name in file_info.get("platform", "") and
                                    architecture in file_info.get("name", "")):
                                    return file_info.get("url", "")
            
            # If exact version not found, try to construct URL
            # Format: cef_binary_{version}_{platform}{arch}_minimal.tar.bz2
            constructed_url = (
                f"{self.CEF_DOWNLOAD_BASE}/"
                f"cef_binary_{version}_{platform_name}{architecture}_minimal.tar.bz2"
            )
            
            self.logger.log(f"Exact match not found, trying: {constructed_url}")
            return constructed_url
            
        except Exception as e:
            self.logger.log(f"Error fetching CEF builds index: {e}")
            return None
    
    def download_cef(self, version: str, download_dir: Path, dry_run: bool = False) -> Optional[Path]:
        """Download CEF binary distribution."""
        self.logger.log("=" * 70)
        self.logger.log("Downloading CEF")
        self.logger.log("=" * 70)
        
        download_url = self.get_download_url(version)
        
        if not download_url:
            self.logger.log("✗ Could not determine download URL")
            self.logger.log("=" * 70 + "\n")
            return None
        
        self.logger.log(f"Download URL: {download_url}")
        
        filename = download_url.split("/")[-1]
        download_path = download_dir / filename
        
        if dry_run:
            self.logger.log(f"[DRY RUN] Would download to: {download_path}")
            self.logger.log("=" * 70 + "\n")
            return download_path
        
        try:
            self.logger.log(f"Downloading to: {download_path}")
            
            response = requests.get(download_url, stream=True, timeout=300)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(download_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\rProgress: {progress:.1f}%", end="", flush=True)
            
            print()  # New line after progress
            
            self.logger.log(f"✓ Download complete: {download_path}")
            self.logger.log(f"  Size: {download_path.stat().st_size / (1024*1024):.2f} MB")
            self.logger.log("=" * 70 + "\n")
            
            return download_path
            
        except Exception as e:
            self.logger.log(f"✗ Download failed: {e}", level="ERROR")
            self.logger.log("=" * 70 + "\n")
            return None


class CEFInstaller:
    """Handles CEF installation and upgrade."""
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self.os_type = platform.system()
    
    def extract_archive(self, archive_path: Path, extract_dir: Path, dry_run: bool = False) -> bool:
        """Extract CEF archive."""
        self.logger.log("=" * 70)
        self.logger.log("Extracting CEF Archive")
        self.logger.log("=" * 70)
        
        if dry_run:
            self.logger.log(f"[DRY RUN] Would extract {archive_path} to {extract_dir}")
            self.logger.log("=" * 70 + "\n")
            return True
        
        try:
            extract_dir.mkdir(parents=True, exist_ok=True)
            
            if archive_path.suffix == ".zip":
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
            elif archive_path.suffix in [".bz2", ".gz", ".tar"]:
                with tarfile.open(archive_path, 'r:*') as tar_ref:
                    tar_ref.extractall(extract_dir)
            else:
                self.logger.log(f"✗ Unsupported archive format: {archive_path.suffix}")
                return False
            
            self.logger.log(f"✓ Extracted to: {extract_dir}")
            self.logger.log("=" * 70 + "\n")
            return True
            
        except Exception as e:
            self.logger.log(f"✗ Extraction failed: {e}", level="ERROR")
            self.logger.log("=" * 70 + "\n")
            return False
    
    def install_cef(self, source_dir: Path, target_dir: Path, dry_run: bool = False) -> bool:
        """Install CEF to target directory."""
        self.logger.log("=" * 70)
        self.logger.log("Installing CEF")
        self.logger.log("=" * 70)
        
        if dry_run:
            self.logger.log(f"[DRY RUN] Would install from {source_dir} to {target_dir}")
            self.logger.log("=" * 70 + "\n")
            return True
        
        try:
            # Find the actual CEF directory (might be nested)
            cef_dir = self._find_cef_directory(source_dir)
            
            if not cef_dir:
                self.logger.log("✗ Could not find CEF directory in extracted files")
                return False
            
            self.logger.log(f"Installing from: {cef_dir}")
            self.logger.log(f"Installing to: {target_dir}")
            
            # Copy CEF files to target
            if target_dir.exists():
                self.logger.log("Removing existing installation...")
                shutil.rmtree(target_dir)
            
            shutil.copytree(cef_dir, target_dir)
            
            self.logger.log(f"✓ CEF installed successfully")
            self.logger.log("=" * 70 + "\n")
            return True
            
        except Exception as e:
            self.logger.log(f"✗ Installation failed: {e}", level="ERROR")
            self.logger.log("=" * 70 + "\n")
            return False
    
    def _find_cef_directory(self, search_dir: Path) -> Optional[Path]:
        """Find the CEF directory in extracted files."""
        # Look for directories containing CEF indicators
        for root, dirs, files in os.walk(search_dir):
            if any(f in files for f in ["libcef.dll", "libcef.so", "libcef.dylib"]):
                return Path(root)
            
            # Check for Release or Debug directories
            for subdir in ["Release", "Debug", "Resources"]:
                if subdir in dirs:
                    potential_path = Path(root) / subdir
                    if any((potential_path / f).exists() for f in ["libcef.dll", "libcef.so", "libcef.dylib"]):
                        return Path(root)
        
        return None


class CEFVerifier:
    """Verifies CEF installation."""
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self.os_type = platform.system()
    
    def verify_installation(self, cef_dir: Path, dry_run: bool = False) -> bool:
        """Verify CEF installation is valid."""
        self.logger.log("=" * 70)
        self.logger.log("Verifying CEF Installation")
        self.logger.log("=" * 70)
        
        if dry_run:
            self.logger.log("[DRY RUN] Would verify installation")
            self.logger.log("=" * 70 + "\n")
            return True
        
        checks_passed = 0
        checks_total = 0
        
        # Check 1: Core library exists
        checks_total += 1
        lib_names = {
            "Windows": "libcef.dll",
            "Darwin": "libcef.dylib",
            "Linux": "libcef.so"
        }
        lib_name = lib_names.get(self.os_type, "libcef.so")
        
        lib_path = self._find_file(cef_dir, lib_name)
        if lib_path:
            self.logger.log(f"✓ Core library found: {lib_path}")
            checks_passed += 1
        else:
            self.logger.log(f"✗ Core library not found: {lib_name}")
        
        # Check 2: Resources exist
        checks_total += 1
        required_resources = ["cef.pak", "cef_100_percent.pak", "cef_200_percent.pak"]
        resources_found = 0
        
        for resource in required_resources:
            if self._find_file(cef_dir, resource):
                resources_found += 1
        
        if resources_found >= 1:  # At least one resource file
            self.logger.log(f"✓ Resources found: {resources_found}/{len(required_resources)}")
            checks_passed += 1
        else:
            self.logger.log(f"✗ Resources not found")
        
        # Check 3: Locales directory
        checks_total += 1
        locales_dir = self._find_directory(cef_dir, "locales")
        if locales_dir:
            locale_count = len(list(locales_dir.glob("*.pak")))
            self.logger.log(f"✓ Locales directory found with {locale_count} locales")
            checks_passed += 1
        else:
            self.logger.log(f"✗ Locales directory not found")
        
        # Summary
        self.logger.log(f"\nVerification: {checks_passed}/{checks_total} checks passed")
        
        success = checks_passed == checks_total
        if success:
            self.logger.log("✓ Installation verified successfully")
        else:
            self.logger.log("⚠ Installation verification incomplete")
        
        self.logger.log("=" * 70 + "\n")
        return success
    
    def _find_file(self, directory: Path, filename: str) -> Optional[Path]:
        """Find a file in directory tree."""
        for root, dirs, files in os.walk(directory):
            if filename in files:
                return Path(root) / filename
        return None
    
    def _find_directory(self, directory: Path, dirname: str) -> Optional[Path]:
        """Find a directory in directory tree."""
        for root, dirs, files in os.walk(directory):
            if dirname in dirs:
                return Path(root) / dirname
        return None


class ReportGenerator:
    """Generates upgrade reports."""
    
    def __init__(self, logger: Logger, log_dir: Path):
        self.logger = logger
        self.log_dir = log_dir
    
    def generate_report(self, results: Dict):
        """Generate a comprehensive upgrade report."""
        report_path = self.log_dir / "README.md"
        
        report_content = f"""# CEF Upgrade Report

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Summary

- **Target Version**: {results.get('target_version', 'N/A')}
- **Dry Run**: {results.get('dry_run', False)}
- **Status**: {results.get('status', 'Unknown')}

## Detection Results

{self._format_detection_results(results.get('detection', {}))}

## Vulnerability Check

{self._format_vulnerability_results(results.get('vulnerabilities', {}))}

## Backup

{self._format_backup_results(results.get('backup', {}))}

## Download

{self._format_download_results(results.get('download', {}))}

## Installation

{self._format_installation_results(results.get('installation', {}))}

## Verification

{self._format_verification_results(results.get('verification', {}))}

## Rollback Instructions

If you need to rollback this upgrade:

1. Stop any applications using CEF
2. Restore from backup:
   ```bash
   tar -xzf {results.get('backup', {}).get('path', 'backup.tar.gz')} -C /
   ```
3. Restart your applications

## Logs

- Commands Log: `{self.log_dir / 'commands.log'}`
- JSONL Log: `{self.log_dir / 'agent-run.jsonl'}`

## Next Steps

{self._format_next_steps(results)}
"""
        
        report_path.write_text(report_content, encoding="utf-8")
        self.logger.log(f"Report generated: {report_path}")
    
    def _format_detection_results(self, detection: Dict) -> str:
        if not detection:
            return "No detection performed"
        
        if detection.get('found'):
            return f"""
- **Found**: Yes
- **Version**: {detection.get('version', 'Unknown')}
- **Chromium Version**: {detection.get('chromium_version', 'Unknown')}
- **Architecture**: {detection.get('architecture', 'Unknown')}
- **Paths**: {', '.join(str(p) for p in detection.get('paths', []))}
"""
        else:
            return "- **Found**: No existing CEF installation detected"
    
    def _format_vulnerability_results(self, vulns: Dict) -> str:
        if not vulns:
            return "No vulnerability check performed"
        
        if vulns.get('has_critical'):
            return f"""
- **Status**: ❌ CRITICAL VULNERABILITIES FOUND
- **Count**: {len(vulns.get('list', []))}
- **Action**: Upgrade aborted
"""
        elif vulns.get('list'):
            return f"""
- **Status**: ⚠ Minor vulnerabilities found
- **Count**: {len(vulns.get('list', []))}
- **Action**: Proceeded with caution
"""
        else:
            return "- **Status**: ✓ No known vulnerabilities"
    
    def _format_backup_results(self, backup: Dict) -> str:
        if not backup:
            return "No backup created"
        
        if backup.get('path'):
            return f"""
- **Path**: `{backup['path']}`
- **Size**: {backup.get('size_mb', 0):.2f} MB
"""
        else:
            return "- **Status**: Backup failed or skipped"
    
    def _format_download_results(self, download: Dict) -> str:
        if not download:
            return "No download performed"
        
        if download.get('path'):
            return f"""
- **Path**: `{download['path']}`
- **URL**: {download.get('url', 'N/A')}
"""
        else:
            return "- **Status**: Download failed or skipped"
    
    def _format_installation_results(self, installation: Dict) -> str:
        if not installation:
            return "No installation performed"
        
        if installation.get('success'):
            return f"""
- **Status**: ✓ Success
- **Target Directory**: `{installation.get('target_dir', 'N/A')}`
"""
        else:
            return f"""
- **Status**: ✗ Failed
- **Error**: {installation.get('error', 'Unknown error')}
"""
    
    def _format_verification_results(self, verification: Dict) -> str:
        if not verification:
            return "No verification performed"
        
        if verification.get('success'):
            return f"""
- **Status**: ✓ Passed
- **Checks**: {verification.get('checks_passed', 0)}/{verification.get('checks_total', 0)}
"""
        else:
            return f"""
- **Status**: ⚠ Incomplete
- **Checks**: {verification.get('checks_passed', 0)}/{verification.get('checks_total', 0)}
"""
    
    def _format_next_steps(self, results: Dict) -> str:
        if results.get('dry_run'):
            return """
This was a dry run. To perform the actual upgrade:
1. Review this report
2. Run the agent again without `--dry-run`
"""
        elif results.get('status') == 'success':
            return """
1. Test your application with the new CEF version
2. Monitor for any compatibility issues
3. Keep the backup until you're confident the upgrade is stable
"""
        else:
            return """
1. Review the error logs
2. Check the troubleshooting section in the documentation
3. Consider trying a different CEF version
"""


class CEFUpgradeAgent:
    """Main agent orchestrating the CEF upgrade process."""
    
    def __init__(self, args):
        self.args = args
        
        # Setup directories
        self.log_dir = Path(args.log_dir) / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = Path(args.backup_dir)
        self.download_dir = Path("temp/cef-downloads")
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.logger = Logger(self.log_dir)
        self.vuln_checker = VulnerabilityChecker(self.logger)
        self.detector = CEFDetector(self.logger)
        self.backup = CEFBackup(self.logger, self.backup_dir)
        self.downloader = CEFDownloader(self.logger)
        self.installer = CEFInstaller(self.logger)
        self.verifier = CEFVerifier(self.logger)
        self.reporter = ReportGenerator(self.logger, self.log_dir)
        
        # Results tracking
        self.results = {
            'target_version': args.target_version,
            'dry_run': args.dry_run,
            'status': 'pending'
        }
    
    def run(self):
        """Execute the upgrade process."""
        self.logger.log("=" * 70)
        self.logger.log("CEF Upgrade Agent")
        self.logger.log("=" * 70)
        self.logger.log(f"Target Version: {self.args.target_version}")
        self.logger.log(f"Dry Run: {self.args.dry_run}")
        self.logger.log(f"App Path: {self.args.app_path or 'System-wide'}")
        self.logger.log("=" * 70 + "\n")
        
        try:
            # Step 1: Vulnerability Check
            has_critical, vulns = self.vuln_checker.check_version(self.args.target_version)
            self.results['vulnerabilities'] = {
                'has_critical': has_critical,
                'list': vulns
            }
            
            if has_critical:
                self.results['status'] = 'aborted_vulnerabilities'
                self.reporter.generate_report(self.results)
                return 1
            
            # Step 2: Detection
            detection = self.detector.detect_cef_in_path(self.args.app_path)
            self.results['detection'] = detection
            
            # Step 3: Backup
            if detection['found'] and detection['paths']:
                backup_path = self.backup.create_backup(detection['paths'], self.args.dry_run)
                self.results['backup'] = {
                    'path': backup_path,
                    'size_mb': backup_path.stat().st_size / (1024*1024) if backup_path and backup_path.exists() else 0
                }
            
            # Step 4: Download
            download_path = self.downloader.download_cef(
                self.args.target_version,
                self.download_dir,
                self.args.dry_run
            )
            
            if not download_path:
                self.results['status'] = 'failed_download'
                self.reporter.generate_report(self.results)
                return 1
            
            self.results['download'] = {
                'path': download_path,
                'url': self.downloader.get_download_url(self.args.target_version)
            }
            
            # Step 5: Extract
            extract_dir = self.download_dir / "extracted"
            if not self.installer.extract_archive(download_path, extract_dir, self.args.dry_run):
                self.results['status'] = 'failed_extraction'
                self.reporter.generate_report(self.results)
                return 1
            
            # Step 6: Install
            target_dir = Path(self.args.install_dir) if self.args.install_dir else Path("cef_installation")
            install_success = self.installer.install_cef(extract_dir, target_dir, self.args.dry_run)
            
            self.results['installation'] = {
                'success': install_success,
                'target_dir': target_dir
            }
            
            if not install_success:
                self.results['status'] = 'failed_installation'
                self.reporter.generate_report(self.results)
                return 1
            
            # Step 7: Verify
            verify_success = self.verifier.verify_installation(target_dir, self.args.dry_run)
            self.results['verification'] = {
                'success': verify_success,
                'checks_passed': 3 if verify_success else 0,
                'checks_total': 3
            }
            
            # Final status
            self.results['status'] = 'success' if verify_success else 'success_with_warnings'
            
            # Generate report
            self.reporter.generate_report(self.results)
            
            self.logger.log("=" * 70)
            self.logger.log("✓ CEF Upgrade Agent Completed")
            self.logger.log(f"Status: {self.results['status']}")
            self.logger.log(f"Report: {self.log_dir / 'README.md'}")
            self.logger.log("=" * 70)
            
            return 0
            
        except Exception as e:
            self.logger.log(f"✗ Fatal error: {e}", level="ERROR")
            self.results['status'] = 'error'
            self.results['error'] = str(e)
            self.reporter.generate_report(self.results)
            return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="CEF (Chromium Embedded Framework) Upgrade Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to see what would happen
  python cef_upgrade_agent.py --target-version 120.1.10+g3ce3184+chromium-120.0.6099.129 --dry-run
  
  # Upgrade CEF in a specific application
  python cef_upgrade_agent.py --target-version 120.1.10+g3ce3184+chromium-120.0.6099.129 --app-path /path/to/app
  
  # Install to custom directory
  python cef_upgrade_agent.py --target-version 120.1.10+g3ce3184+chromium-120.0.6099.129 --install-dir /opt/cef
"""
    )
    
    parser.add_argument(
        "--target-version",
        required=True,
        help="CEF version to install (e.g., '120.1.10+g3ce3184+chromium-120.0.6099.129')"
    )
    
    parser.add_argument(
        "--app-path",
        help="Path to application using CEF (for detection and upgrade)"
    )
    
    parser.add_argument(
        "--install-dir",
        help="Directory to install CEF (default: ./cef_installation)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the process without making changes"
    )
    
    parser.add_argument(
        "--backup-dir",
        default="temp/cef-agent-backups",
        help="Directory to store backups (default: temp/cef-agent-backups)"
    )
    
    parser.add_argument(
        "--log-dir",
        default="temp/cef-agent-logs",
        help="Directory to store logs (default: temp/cef-agent-logs)"
    )
    
    args = parser.parse_args()
    
    # Run the agent
    agent = CEFUpgradeAgent(args)
    exit_code = agent.run()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
