#!/usr/bin/env python3
"""
Test script for CEF Build Agent

Tests the build automation functionality including:
- CMake download and extraction
- CMake configuration
- Visual Studio project modification
- MSBuild execution
- Binary collection
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from cef_build_agent import (
    Logger,
    CMakeDownloader,
    CMakeConfigurator,
    VSProjectModifier,
    VSBuilder,
    BinaryCollector
)


class TestLogger(unittest.TestCase):
    """Test Logger functionality."""
    
    def setUp(self):
        self.log_dir = Path("temp/test-logs")
        self.logger = Logger(self.log_dir)
    
    def test_logger_creation(self):
        """Test logger creates necessary files."""
        self.assertTrue(self.log_dir.exists())
        self.assertTrue((self.log_dir / "build-commands.log").exists())
        self.assertTrue((self.log_dir / "build-run.jsonl").exists())
    
    def test_logging(self):
        """Test basic logging functionality."""
        self.logger.log("Test message", "INFO")
        
        # Check log file contains message
        log_content = (self.log_dir / "build-commands.log").read_text()
        self.assertIn("Test message", log_content)


class TestCMakeDownloader(unittest.TestCase):
    """Test CMake downloader."""
    
    def setUp(self):
        self.log_dir = Path("temp/test-logs")
        self.logger = Logger(self.log_dir)
        self.downloader = CMakeDownloader(self.logger)
    
    def test_get_download_url(self):
        """Test CMake download URL generation."""
        url = self.downloader.get_cmake_download_url("3.30.1")
        self.assertIsNotNone(url)
        self.assertIn("cmake", url.lower())
        self.assertIn("3.30.1", url)
    
    @patch('cef_build_agent.REQUESTS_AVAILABLE', False)
    def test_download_without_requests(self):
        """Test download fails gracefully without requests library."""
        result = self.downloader.download_cmake("3.30.1", Path("temp/downloads"))
        self.assertIsNone(result)


class TestCMakeConfigurator(unittest.TestCase):
    """Test CMake configurator."""
    
    def setUp(self):
        self.log_dir = Path("temp/test-logs")
        self.logger = Logger(self.log_dir)
        self.cmake_path = Path("cmake")  # Dummy path
        self.configurator = CMakeConfigurator(self.logger, self.cmake_path)
    
    def test_vs_generator_detection(self):
        """Test Visual Studio generator detection."""
        generator = self.configurator._detect_vs_generator()
        self.assertIsNotNone(generator)
        self.assertIn("Visual Studio", generator)
    
    def test_configure_dry_run(self):
        """Test configure in dry-run mode."""
        result = self.configurator.configure(
            Path("source"),
            Path("build"),
            "Visual Studio 17 2022",
            "x64",
            dry_run=True
        )
        self.assertTrue(result)


class TestVSProjectModifier(unittest.TestCase):
    """Test Visual Studio project modifier."""
    
    def setUp(self):
        self.log_dir = Path("temp/test-logs")
        self.logger = Logger(self.log_dir)
        self.modifier = VSProjectModifier(self.logger)
    
    def test_modify_dry_run(self):
        """Test project modification in dry-run mode."""
        result = self.modifier.modify_runtime_library(
            Path("dummy.vcxproj"),
            "MultiThreadedDLL",
            dry_run=True
        )
        self.assertTrue(result)


class TestVSBuilder(unittest.TestCase):
    """Test Visual Studio builder."""
    
    def setUp(self):
        self.log_dir = Path("temp/test-logs")
        self.logger = Logger(self.log_dir)
        self.builder = VSBuilder(self.logger)
    
    def test_msbuild_detection(self):
        """Test MSBuild path detection."""
        # This will be None if VS is not installed, which is OK for testing
        msbuild = self.builder._find_msbuild()
        # Just verify it returns a Path or None
        self.assertTrue(msbuild is None or isinstance(msbuild, Path))
    
    def test_build_dry_run(self):
        """Test build in dry-run mode."""
        result = self.builder.build_project(
            Path("dummy.sln"),
            "Release",
            "x64",
            dry_run=True
        )
        self.assertTrue(result)


class TestBinaryCollector(unittest.TestCase):
    """Test binary collector."""
    
    def setUp(self):
        self.log_dir = Path("temp/test-logs")
        self.logger = Logger(self.log_dir)
        self.collector = BinaryCollector(self.logger)
    
    def test_collect_dry_run(self):
        """Test binary collection in dry-run mode."""
        result = self.collector.collect_binaries(
            Path("cef_source"),
            Path("build"),
            Path("output"),
            dry_run=True
        )
        self.assertTrue(result)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete workflow."""
    
    def test_dry_run_workflow(self):
        """Test complete workflow in dry-run mode."""
        from cef_build_agent import CEFBuildAgent
        import argparse
        
        # Create mock args
        args = argparse.Namespace(
            cef_source="temp/test-cef",
            output_dir="temp/test-output",
            cmake_path=None,
            cmake_version="3.30.1",
            vs_generator="Visual Studio 17 2022",
            platform="x64",
            dry_run=True,
            log_dir="temp/test-build-logs"
        )
        
        # Create dummy CEF source directory
        cef_source = Path("temp/test-cef")
        cef_source.mkdir(parents=True, exist_ok=True)
        
        # Run agent
        agent = CEFBuildAgent(args)
        exit_code = agent.run()
        
        # In dry-run mode, should succeed
        self.assertEqual(exit_code, 0)


def run_tests():
    """Run all tests."""
    print("=" * 70)
    print("CEF Build Agent - Test Suite")
    print("=" * 70)
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestLogger))
    suite.addTests(loader.loadTestsFromTestCase(TestCMakeDownloader))
    suite.addTests(loader.loadTestsFromTestCase(TestCMakeConfigurator))
    suite.addTests(loader.loadTestsFromTestCase(TestVSProjectModifier))
    suite.addTests(loader.loadTestsFromTestCase(TestVSBuilder))
    suite.addTests(loader.loadTestsFromTestCase(TestBinaryCollector))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print()
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
