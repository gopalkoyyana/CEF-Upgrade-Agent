#!/usr/bin/env python3
"""
CEF Unified Agent - Complete Download and Build Automation

This unified agent combines the functionality of both:
- cef_upgrade_agent.py (download and install CEF binaries)
- cef_build_agent.py (build libcef_dll_wrapper from source)

Configuration is read from cef_config.json instead of hardcoded values.

Usage:
    python cef_unified_agent.py                    # Use config file
    python cef_unified_agent.py --config custom.json  # Custom config
    python cef_unified_agent.py --dry-run          # Test without changes
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

# Import components from both agents
sys.path.insert(0, str(Path(__file__).parent))

try:
    from cef_upgrade_agent import (
        Logger as UpgradeLogger,
        VulnerabilityChecker,
        CEFDetector,
        CEFBackup,
        CEFDownloader,
        CEFInstaller,
        CEFVerifier,
        REQUESTS_AVAILABLE
    )
    UPGRADE_AGENT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import upgrade agent components: {e}")
    UPGRADE_AGENT_AVAILABLE = False

try:
    from cef_build_agent import (
        Logger as BuildLogger,
        CMakeDownloader,
        CMakeConfigurator,
        VSProjectModifier,
        VSBuilder,
        BinaryCollector
    )
    BUILD_AGENT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import build agent components: {e}")
    BUILD_AGENT_AVAILABLE = False

try:
    from cef_mfc_integration import integrate_with_mfc, MFCIntegration
    MFC_INTEGRATION_AVAILABLE = True
except ImportError as e:
    print(f"Info: MFC integration not available: {e}")
    MFC_INTEGRATION_AVAILABLE = False


class ConfigManager:
    """Manages configuration loading and validation."""
    
    DEFAULT_CONFIG = {
        "cef_version": "140.1.13+g5eb3258+chromium-140.0.7339.41",
        "platform": "windows64",
        "architecture": "x64",
        "build_configuration": "Release",
        "cmake_version": "3.30.1",
        "vs_generator": "Visual Studio 17 2022",
        "output_directory": "bin/NT/cef/release",
        "temp_directory": "temp/cef-workflow",
        "runtime_library": "MultiThreadedDLL"
    }
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("cef_config.json")
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Load configuration from file or create default."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                print(f"✓ Loaded configuration from: {self.config_path}")
                return {**self.DEFAULT_CONFIG, **config}  # Merge with defaults
            except Exception as e:
                print(f"⚠ Error loading config: {e}")
                print("Using default configuration")
                return self.DEFAULT_CONFIG.copy()
        else:
            print(f"⚠ Config file not found: {self.config_path}")
            print("Creating default configuration...")
            self.save_config(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG.copy()
    
    def save_config(self, config: Dict):
        """Save configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"✓ Configuration saved to: {self.config_path}")
        except Exception as e:
            print(f"✗ Error saving config: {e}")
    
    def get(self, key: str, default=None):
        """Get configuration value."""
        return self.config.get(key, default)
    
    def display(self):
        """Display current configuration."""
        print("\n" + "=" * 70)
        print("CONFIGURATION")
        print("=" * 70)
        for key, value in self.config.items():
            print(f"  {key:25s}: {value}")
        print("=" * 70 + "\n")


class UnifiedLogger:
    """Unified logger for both phases."""
    
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.commands_log = log_dir / "unified-commands.log"
        self.jsonl_log = log_dir / "unified-run.jsonl"
        
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


class CEFUnifiedAgent:
    """Unified agent that handles complete CEF download and build workflow."""
    
    def __init__(self, config_manager: ConfigManager, args):
        self.config = config_manager
        self.args = args
        
        # Setup directories
        self.log_dir = Path("temp/cef-unified-logs") / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.temp_dir = Path(self.config.get("temp_directory", "temp/cef-workflow"))
        self.output_dir = Path(self.config.get("output_directory", "bin/NT/cef/release"))
        
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.cef_install_dir = self.temp_dir / "cef_source"
        
        # Initialize logger
        self.logger = UnifiedLogger(self.log_dir)
        
        # Results tracking
        self.results = {
            'config': self.config.config,
            'dry_run': args.dry_run,
            'phase1_status': 'pending',
            'phase2_status': 'pending',
            'overall_status': 'pending'
        }
    
    def run(self):
        """Execute the complete workflow."""
        self.logger.log("=" * 70)
        self.logger.log("CEF UNIFIED AGENT - Complete Download & Build Workflow")
        self.logger.log("=" * 70)
        self.logger.log(f"Version: 2.0.0")
        self.logger.log(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.log("=" * 70)
        
        # Display configuration
        self.config.display()
        
        self.logger.log(f"CEF Version: {self.config.get('cef_version')}")
        self.logger.log(f"Output Directory: {self.output_dir}")
        self.logger.log(f"Dry Run: {self.args.dry_run}")
        self.logger.log("=" * 70 + "\n")
        
        try:
            # Phase 1: Download and Install CEF
            if not self.args.skip_download:
                if not self.run_phase1_download():
                    self.logger.log("✗ Phase 1 (Download) failed", level="ERROR")
                    self.results['overall_status'] = 'failed_phase1'
                    return 1
                self.results['phase1_status'] = 'success'
            else:
                self.logger.log("⊘ Skipping Phase 1 (Download) as requested")
                self.results['phase1_status'] = 'skipped'
            
            # Phase 2: Build libcef_dll_wrapper
            if not self.args.skip_build:
                if not self.run_phase2_build():
                    self.logger.log("✗ Phase 2 (Build) failed", level="ERROR")
                    self.results['overall_status'] = 'failed_phase2'
                    return 1
                self.results['phase2_status'] = 'success'
            else:
                self.logger.log("⊘ Skipping Phase 2 (Build) as requested")
                self.results['phase2_status'] = 'skipped'
            
            # Phase 3: MFC Integration (optional)
            if MFC_INTEGRATION_AVAILABLE and self.config.get('enable_mfc_integration', False):
                if not integrate_with_mfc(self, self.args.dry_run):
                    self.logger.log("⚠ MFC integration had issues (continuing anyway)", level="WARNING")
                    self.results['phase3_status'] = 'warning'
                else:
                    self.results['phase3_status'] = 'success'
            else:
                self.results['phase3_status'] = 'skipped'
            
            # Success!
            self.results['overall_status'] = 'success'
            self.print_success_summary()
            return 0
            
        except Exception as e:
            self.logger.log(f"✗ Fatal error: {e}", level="ERROR")
            self.results['overall_status'] = 'error'
            self.results['error'] = str(e)
            return 1
    
    def run_phase1_download(self) -> bool:
        """Phase 1: Download and install CEF binaries."""
        self.logger.log("\n" + "=" * 70)
        self.logger.log("PHASE 1: DOWNLOAD & INSTALL CEF BINARIES")
        self.logger.log("=" * 70 + "\n")
        
        if not UPGRADE_AGENT_AVAILABLE:
            self.logger.log("✗ Upgrade agent components not available", level="ERROR")
            return False
        
        # Build command for upgrade agent
        cmd = [
            sys.executable,
            "cef_upgrade_agent.py",
            "--target-version", self.config.get('cef_version'),
            "--install-dir", str(self.cef_install_dir),
            "--log-dir", str(self.log_dir / "phase1-logs"),
        ]
        
        if self.args.dry_run:
            cmd.append("--dry-run")
        
        self.logger.log(f"Running: {' '.join(cmd)}\n")
        
        result = subprocess.run(cmd, capture_output=False, text=True)
        
        if result.returncode != 0:
            self.logger.log(f"\n✗ Phase 1 failed with exit code {result.returncode}", level="ERROR")
            return False
        
        self.logger.log("\n✓ Phase 1 completed successfully\n")
        return True
    
    def run_phase2_build(self) -> bool:
        """Phase 2: Build libcef_dll_wrapper."""
        self.logger.log("\n" + "=" * 70)
        self.logger.log("PHASE 2: BUILD LIBCEF_DLL_WRAPPER")
        self.logger.log("=" * 70 + "\n")
        
        if not BUILD_AGENT_AVAILABLE:
            self.logger.log("✗ Build agent components not available", level="ERROR")
            return False
        
        # Find CEF source directory
        if not self.args.dry_run:
            cef_source_dirs = list(self.cef_install_dir.glob("cef_binary_*"))
            if not cef_source_dirs:
                # Try the install dir itself
                if self.cef_install_dir.exists():
                    cef_source = self.cef_install_dir
                else:
                    self.logger.log(f"✗ CEF source not found in {self.cef_install_dir}", level="ERROR")
                    return False
            else:
                cef_source = cef_source_dirs[0]
        else:
            cef_source = self.cef_install_dir
        
        # Build command for build agent
        cmd = [
            sys.executable,
            "cef_build_agent.py",
            "--cef-source", str(cef_source),
            "--output-dir", str(self.output_dir),
            "--cmake-version", self.config.get('cmake_version'),
            "--platform", self.config.get('architecture'),
            "--log-dir", str(self.log_dir / "phase2-logs"),
        ]
        
        # Add VS generator if specified
        vs_generator = self.config.get('vs_generator')
        if vs_generator:
            cmd.extend(["--vs-generator", vs_generator])
        
        if self.args.dry_run:
            cmd.append("--dry-run")
        
        self.logger.log(f"Running: {' '.join(cmd)}\n")
        
        result = subprocess.run(cmd, capture_output=False, text=True)
        
        if result.returncode != 0:
            self.logger.log(f"\n✗ Phase 2 failed with exit code {result.returncode}", level="ERROR")
            return False
        
        self.logger.log("\n✓ Phase 2 completed successfully\n")
        return True
    
    def print_success_summary(self):
        """Print success summary."""
        self.logger.log("\n" + "=" * 70)
        self.logger.log("✓ CEF UNIFIED AGENT COMPLETED SUCCESSFULLY")
        self.logger.log("=" * 70)
        self.logger.log(f"\nCEF Version: {self.config.get('cef_version')}")
        self.logger.log(f"Output Directory: {self.output_dir}")
        self.logger.log(f"\nPhase 1 (Download): {self.results['phase1_status']}")
        self.logger.log(f"Phase 2 (Build): {self.results['phase2_status']}")
        self.logger.log(f"\nLogs Directory: {self.log_dir}")
        
        if not self.args.dry_run:
            self.logger.log(f"\n📦 Output Contents:")
            self.logger.log(f"  {self.output_dir}/")
            self.logger.log(f"  ├── include/              # CEF headers")
            self.logger.log(f"  ├── libcef.dll            # Main CEF library")
            self.logger.log(f"  ├── libcef_dll_wrapper.lib # Compiled wrapper")
            self.logger.log(f"  ├── *.pak files           # Resources")
            self.logger.log(f"  └── locales/              # Locale files")
            
            self.logger.log(f"\n📝 Next Steps:")
            self.logger.log(f"  1. Link your application with libcef_dll_wrapper.lib")
            self.logger.log(f"  2. Include headers from {self.output_dir}/include/")
            self.logger.log(f"  3. Deploy runtime binaries with your application")
        
        self.logger.log("\n" + "=" * 70 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="CEF Unified Agent - Complete Download & Build Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Configuration:
  The agent reads settings from cef_config.json by default.
  You can specify a custom config file with --config.

Examples:
  # Use default config (cef_config.json)
  python cef_unified_agent.py

  # Use custom config
  python cef_unified_agent.py --config my_config.json

  # Dry run to preview actions
  python cef_unified_agent.py --dry-run

  # Skip download (use existing CEF)
  python cef_unified_agent.py --skip-download

  # Only download, skip build
  python cef_unified_agent.py --skip-build

Configuration File Format (cef_config.json):
  {
    "cef_version": "140.1.13+g5eb3258+chromium-140.0.7339.41",
    "platform": "windows64",
    "architecture": "x64",
    "build_configuration": "Release",
    "cmake_version": "3.30.1",
    "vs_generator": "Visual Studio 17 2022",
    "output_directory": "bin/NT/cef/release",
    "temp_directory": "temp/cef-workflow",
    "runtime_library": "MultiThreadedDLL"
  }
"""
    )
    
    parser.add_argument(
        "--config",
        help="Path to configuration file (default: cef_config.json)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the process without making changes"
    )
    
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip Phase 1 (download), use existing CEF source"
    )
    
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip Phase 2 (build), only download CEF"
    )
    
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="Display current configuration and exit"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config_path = Path(args.config) if args.config else None
    config_manager = ConfigManager(config_path)
    
    # Show config and exit if requested
    if args.show_config:
        config_manager.display()
        return 0
    
    # Validate required components
    if not UPGRADE_AGENT_AVAILABLE and not args.skip_download:
        print("ERROR: Upgrade agent components not available.")
        print("Please ensure cef_upgrade_agent.py is in the same directory.")
        return 1
    
    if not BUILD_AGENT_AVAILABLE and not args.skip_build:
        print("ERROR: Build agent components not available.")
        print("Please ensure cef_build_agent.py is in the same directory.")
        return 1
    
    # Run the unified agent
    agent = CEFUnifiedAgent(config_manager, args)
    exit_code = agent.run()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
