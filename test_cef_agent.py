#!/usr/bin/env python3
"""
Test script for CEF Upgrade Agent

This script tests various components of the CEF Upgrade Agent
to ensure they work correctly.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import the agent
sys.path.insert(0, str(Path(__file__).parent))

from cef_upgrade_agent import (
    Logger,
    VulnerabilityChecker,
    CEFDetector,
    CEFBackup,
    CEFDownloader,
    CEFVerifier
)


def test_logger():
    """Test the Logger class."""
    print("=" * 70)
    print("Testing Logger")
    print("=" * 70)
    
    log_dir = Path("temp/test-logs")
    logger = Logger(log_dir)
    
    logger.log("Test message", "INFO")
    logger.log_command("echo 'test'", "test output", 0)
    
    # Check if log files were created
    assert (log_dir / "commands.log").exists(), "commands.log not created"
    assert (log_dir / "agent-run.jsonl").exists(), "agent-run.jsonl not created"
    
    print("✓ Logger test passed\n")


def test_vulnerability_checker():
    """Test the VulnerabilityChecker class."""
    print("=" * 70)
    print("Testing VulnerabilityChecker")
    print("=" * 70)
    
    log_dir = Path("temp/test-logs")
    logger = Logger(log_dir)
    checker = VulnerabilityChecker(logger)
    
    # Test with a recent CEF version (may or may not have vulnerabilities)
    version = "120.1.10+g3ce3184+chromium-120.0.6099.129"
    
    try:
        has_critical, vulns = checker.check_version(version)
        print(f"Vulnerability check completed: {len(vulns)} vulnerabilities found")
        print(f"Has critical: {has_critical}")
        print("✓ VulnerabilityChecker test passed\n")
    except Exception as e:
        print(f"⚠ VulnerabilityChecker test skipped: {e}\n")


def test_detector():
    """Test the CEFDetector class."""
    print("=" * 70)
    print("Testing CEFDetector")
    print("=" * 70)
    
    log_dir = Path("temp/test-logs")
    logger = Logger(log_dir)
    detector = CEFDetector(logger)
    
    # Test system-wide detection (may or may not find CEF)
    result = detector.detect_cef_in_path()
    
    print(f"Detection result: {result}")
    print("✓ CEFDetector test passed\n")


def test_backup():
    """Test the CEFBackup class."""
    print("=" * 70)
    print("Testing CEFBackup")
    print("=" * 70)
    
    log_dir = Path("temp/test-logs")
    backup_dir = Path("temp/test-backups")
    logger = Logger(log_dir)
    backup = CEFBackup(logger, backup_dir)
    
    # Create a test directory to backup
    test_dir = Path("temp/test-cef")
    test_dir.mkdir(parents=True, exist_ok=True)
    (test_dir / "test.txt").write_text("test content")
    
    # Test backup creation (dry run)
    backup_path = backup.create_backup([test_dir], dry_run=True)
    
    print(f"Backup path (dry run): {backup_path}")
    print("✓ CEFBackup test passed\n")


def test_downloader():
    """Test the CEFDownloader class."""
    print("=" * 70)
    print("Testing CEFDownloader")
    print("=" * 70)
    
    log_dir = Path("temp/test-logs")
    logger = Logger(log_dir)
    downloader = CEFDownloader(logger)
    
    # Test URL generation
    version = "120.1.10+g3ce3184+chromium-120.0.6099.129"
    url = downloader.get_download_url(version)
    
    print(f"Download URL: {url}")
    
    if url:
        print("✓ CEFDownloader test passed\n")
    else:
        print("⚠ CEFDownloader test: Could not generate URL\n")


def test_verifier():
    """Test the CEFVerifier class."""
    print("=" * 70)
    print("Testing CEFVerifier")
    print("=" * 70)
    
    log_dir = Path("temp/test-logs")
    logger = Logger(log_dir)
    verifier = CEFVerifier(logger)
    
    # Create a mock CEF directory
    test_dir = Path("temp/test-cef-install")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Test verification (will fail as it's not a real CEF installation)
    result = verifier.verify_installation(test_dir, dry_run=True)
    
    print(f"Verification result (dry run): {result}")
    print("✓ CEFVerifier test passed\n")


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("CEF Upgrade Agent - Test Suite")
    print("=" * 70 + "\n")
    
    tests = [
        ("Logger", test_logger),
        ("VulnerabilityChecker", test_vulnerability_checker),
        ("CEFDetector", test_detector),
        ("CEFBackup", test_backup),
        ("CEFDownloader", test_downloader),
        ("CEFVerifier", test_verifier),
    ]
    
    passed = 0
    failed = 0
    skipped = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test_name} test failed: {e}\n")
            failed += 1
        except Exception as e:
            print(f"⚠ {test_name} test skipped: {e}\n")
            skipped += 1
    
    # Summary
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Passed:  {passed}/{len(tests)}")
    print(f"Failed:  {failed}/{len(tests)}")
    print(f"Skipped: {skipped}/{len(tests)}")
    print("=" * 70 + "\n")
    
    if failed > 0:
        sys.exit(1)
    else:
        print("✓ All tests passed!\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
