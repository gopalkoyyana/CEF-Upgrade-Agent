#!/usr/bin/env python3
"""
CEF Build Agent - Automated libcef_dll_wrapper Builder

Automates the complete process of building libcef_dll_wrapper from CEF binaries:
1. Downloads and installs CMake
2. Configures CMake with Visual Studio generator
3. Generates Visual Studio solution
4. Modifies project properties (Runtime Library to /MD)
5. Builds libcef_dll_wrapper project
6. Collects and deploys binaries to target location

Designed to work standalone or in conjunction with cef_upgrade_agent.py
"""

import os
import sys
import argparse
import platform
import subprocess
import shutil
import json
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Optional dependency for downloads
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("WARNING: 'requests' library not found. Download features will be disabled.")
    print("Install with: pip install requests")


class Logger:
    """Handles logging to both console and file."""
    
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.commands_log = log_dir / "build-commands.log"
        self.jsonl_log = log_dir / "build-run.jsonl"
        
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


class CMakeDownloader:
    """Downloads and installs CMake."""
    
    CMAKE_DOWNLOAD_BASE = "https://github.com/Kitware/CMake/releases/download"
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self.os_type = platform.system()
    
    def get_cmake_download_url(self, version: str = "3.30.1") -> Optional[str]:
        """Get CMake download URL for the current platform."""
        if self.os_type == "Windows":
            arch = "x86_64" if platform.machine() in ["AMD64", "x86_64"] else "i386"
            filename = f"cmake-{version}-windows-{arch}.zip"
            return f"{self.CMAKE_DOWNLOAD_BASE}/v{version}/{filename}"
        elif self.os_type == "Darwin":
            return f"{self.CMAKE_DOWNLOAD_BASE}/v{version}/cmake-{version}-macos-universal.tar.gz"
        else:  # Linux
            arch = "x86_64" if platform.machine() in ["AMD64", "x86_64"] else "i386"
            return f"{self.CMAKE_DOWNLOAD_BASE}/v{version}/cmake-{version}-linux-{arch}.tar.gz"
    
    def download_cmake(self, version: str, download_dir: Path, dry_run: bool = False) -> Optional[Path]:
        """Download CMake binary distribution."""
        self.logger.log("=" * 70)
        self.logger.log("Downloading CMake")
        self.logger.log("=" * 70)
        
        if not REQUESTS_AVAILABLE:
            self.logger.log("ERROR: 'requests' library required for downloading")
            return None
        
        download_url = self.get_cmake_download_url(version)
        if not download_url:
            self.logger.log("✗ Could not determine CMake download URL")
            return None
        
        self.logger.log(f"Download URL: {download_url}")
        
        filename = download_url.split("/")[-1]
        download_path = download_dir / filename
        
        if dry_run:
            self.logger.log(f"[DRY RUN] Would download to: {download_path}")
            self.logger.log("=" * 70 + "\n")
            return download_path
        
        # Check if already downloaded
        if download_path.exists():
            self.logger.log(f"✓ CMake already downloaded: {download_path}")
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
    
    def extract_cmake(self, archive_path: Path, extract_dir: Path, dry_run: bool = False) -> Optional[Path]:
        """Extract CMake archive and return path to cmake executable."""
        self.logger.log("=" * 70)
        self.logger.log("Extracting CMake")
        self.logger.log("=" * 70)
        
        if dry_run:
            self.logger.log(f"[DRY RUN] Would extract {archive_path} to {extract_dir}")
            self.logger.log("=" * 70 + "\n")
            return extract_dir / "bin" / "cmake.exe" if self.os_type == "Windows" else extract_dir / "bin" / "cmake"
        
        try:
            extract_dir.mkdir(parents=True, exist_ok=True)
            
            if archive_path.suffix == ".zip":
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
            else:
                import tarfile
                with tarfile.open(archive_path, 'r:*') as tar_ref:
                    tar_ref.extractall(extract_dir)
            
            # Find cmake executable
            cmake_exe = None
            for root, dirs, files in os.walk(extract_dir):
                if "cmake.exe" in files or "cmake" in files:
                    cmake_name = "cmake.exe" if self.os_type == "Windows" else "cmake"
                    cmake_exe = Path(root) / cmake_name
                    break
            
            if cmake_exe and cmake_exe.exists():
                self.logger.log(f"✓ CMake extracted: {cmake_exe}")
                self.logger.log("=" * 70 + "\n")
                return cmake_exe
            else:
                self.logger.log("✗ Could not find cmake executable")
                self.logger.log("=" * 70 + "\n")
                return None
            
        except Exception as e:
            self.logger.log(f"✗ Extraction failed: {e}", level="ERROR")
            self.logger.log("=" * 70 + "\n")
            return None


class CMakeConfigurator:
    """Configures and generates CMake projects."""
    
    def __init__(self, logger: Logger, cmake_path: Path):
        self.logger = logger
        self.cmake_path = cmake_path
        self.os_type = platform.system()
    
    def configure(self, source_dir: Path, build_dir: Path, 
                  generator: str = None, platform_arch: str = "x64", 
                  dry_run: bool = False) -> bool:
        """Run CMake configure step."""
        self.logger.log("=" * 70)
        self.logger.log("CMake Configure")
        self.logger.log("=" * 70)
        
        # Determine generator
        if not generator:
            if self.os_type == "Windows":
                # Try to detect Visual Studio version
                generator = self._detect_vs_generator()
            else:
                generator = "Unix Makefiles"
        
        self.logger.log(f"Source Directory: {source_dir}")
        self.logger.log(f"Build Directory: {build_dir}")
        self.logger.log(f"Generator: {generator}")
        self.logger.log(f"Platform: {platform_arch}")
        
        if dry_run:
            self.logger.log("[DRY RUN] Would run CMake configure")
            self.logger.log("=" * 70 + "\n")
            return True
        
        try:
            build_dir.mkdir(parents=True, exist_ok=True)
            
            cmd = [
                str(self.cmake_path),
                "-S", str(source_dir),
                "-B", str(build_dir),
                "-G", generator,
            ]
            
            if platform_arch and self.os_type == "Windows":
                cmd.extend(["-A", platform_arch])
            
            self.logger.log(f"Running: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(build_dir)
            )
            
            self.logger.log_command(' '.join(cmd), result.stdout + result.stderr, result.returncode)
            
            if result.returncode == 0:
                self.logger.log("✓ CMake configure successful")
                self.logger.log("=" * 70 + "\n")
                return True
            else:
                self.logger.log(f"✗ CMake configure failed with code {result.returncode}", level="ERROR")
                self.logger.log("=" * 70 + "\n")
                return False
                
        except Exception as e:
            self.logger.log(f"✗ CMake configure failed: {e}", level="ERROR")
            self.logger.log("=" * 70 + "\n")
            return False
    
    def generate(self, build_dir: Path, dry_run: bool = False) -> bool:
        """Run CMake generate step (usually automatic with configure)."""
        self.logger.log("=" * 70)
        self.logger.log("CMake Generate")
        self.logger.log("=" * 70)
        
        if dry_run:
            self.logger.log("[DRY RUN] Would run CMake generate")
            self.logger.log("=" * 70 + "\n")
            return True
        
        # In modern CMake, generate happens automatically during configure
        # This is mainly for compatibility
        self.logger.log("✓ Generation completed during configure step")
        self.logger.log("=" * 70 + "\n")
        return True
    
    def _detect_vs_generator(self) -> str:
        """Detect available Visual Studio version."""
        # Check for VS installations in order of preference
        vs_versions = [
            ("Visual Studio 17 2022", "2022"),
            ("Visual Studio 16 2019", "2019"),
            ("Visual Studio 15 2017", "2017"),
            ("Visual Studio 14 2015", "2015"),
        ]
        
        for generator, year in vs_versions:
            # Check if vswhere can find this version
            try:
                vswhere_path = Path(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")) / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"
                if vswhere_path.exists():
                    result = subprocess.run(
                        [str(vswhere_path), "-version", f"[{year[0:2]}.0,{int(year[0:2])+1}.0)", "-property", "installationPath"],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        self.logger.log(f"Detected: {generator}")
                        return generator
            except:
                pass
        
        # Default to VS 2022
        self.logger.log("Using default: Visual Studio 17 2022")
        return "Visual Studio 17 2022"


class VSProjectModifier:
    """Modifies Visual Studio project files."""
    
    def __init__(self, logger: Logger):
        self.logger = logger
    
    def modify_runtime_library(self, vcxproj_path: Path, runtime: str = "MultiThreadedDLL", 
                               dry_run: bool = False) -> bool:
        """Modify Runtime Library setting in .vcxproj file."""
        self.logger.log("=" * 70)
        self.logger.log("Modifying Project Properties")
        self.logger.log("=" * 70)
        self.logger.log(f"Project: {vcxproj_path}")
        self.logger.log(f"Setting Runtime Library to: {runtime} (/MD)")
        
        if dry_run:
            self.logger.log("[DRY RUN] Would modify project properties")
            self.logger.log("=" * 70 + "\n")
            return True
        
        try:
            # Register namespace
            ET.register_namespace('', 'http://schemas.microsoft.com/developer/msbuild/2003')
            
            tree = ET.parse(vcxproj_path)
            root = tree.getroot()
            
            ns = {'ms': 'http://schemas.microsoft.com/developer/msbuild/2003'}
            
            # Find all PropertyGroups with Configuration=Release
            modified = False
            for prop_group in root.findall('.//ms:PropertyGroup[@Label="Configuration"]', ns):
                config = prop_group.get('Condition', '')
                if 'Release' in config:
                    # Find or create RuntimeLibrary element
                    runtime_elem = prop_group.find('ms:RuntimeLibrary', ns)
                    if runtime_elem is None:
                        runtime_elem = ET.SubElement(prop_group, 'RuntimeLibrary')
                    runtime_elem.text = runtime
                    modified = True
            
            # Also check ItemDefinitionGroup
            for item_def in root.findall('.//ms:ItemDefinitionGroup', ns):
                config = item_def.get('Condition', '')
                if 'Release' in config:
                    cl_compile = item_def.find('ms:ClCompile', ns)
                    if cl_compile is None:
                        cl_compile = ET.SubElement(item_def, 'ClCompile')
                    runtime_elem = cl_compile.find('ms:RuntimeLibrary', ns)
                    if runtime_elem is None:
                        runtime_elem = ET.SubElement(cl_compile, 'RuntimeLibrary')
                    runtime_elem.text = runtime
                    modified = True
            
            if modified:
                tree.write(vcxproj_path, encoding='utf-8', xml_declaration=True)
                self.logger.log("✓ Project properties modified successfully")
            else:
                self.logger.log("⚠ No Release configuration found to modify")
            
            self.logger.log("=" * 70 + "\n")
            return True
            
        except Exception as e:
            self.logger.log(f"✗ Failed to modify project: {e}", level="ERROR")
            self.logger.log("=" * 70 + "\n")
            return False


class VSBuilder:
    """Builds Visual Studio projects using MSBuild."""
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self.msbuild_path = self._find_msbuild()
    
    def _find_msbuild(self) -> Optional[Path]:
        """Find MSBuild executable."""
        # Try vswhere first
        try:
            vswhere_path = Path(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")) / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"
            if vswhere_path.exists():
                result = subprocess.run(
                    [str(vswhere_path), "-latest", "-requires", "Microsoft.Component.MSBuild", "-find", "MSBuild\\**\\Bin\\MSBuild.exe"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0 and result.stdout.strip():
                    msbuild = Path(result.stdout.strip().split('\n')[0])
                    if msbuild.exists():
                        return msbuild
        except:
            pass
        
        # Fallback to common locations
        common_paths = [
            Path(r"C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe"),
            Path(r"C:\Program Files\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\MSBuild.exe"),
            Path(r"C:\Program Files\Microsoft Visual Studio\2022\Enterprise\MSBuild\Current\Bin\MSBuild.exe"),
            Path(r"C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\MSBuild\Current\Bin\MSBuild.exe"),
        ]
        
        for path in common_paths:
            if path.exists():
                return path
        
        return None
    
    def build_project(self, solution_or_project: Path, configuration: str = "Release", 
                     platform: str = "x64", target: str = None, dry_run: bool = False) -> bool:
        """Build a Visual Studio solution or project."""
        self.logger.log("=" * 70)
        self.logger.log("Building Project")
        self.logger.log("=" * 70)
        self.logger.log(f"Solution/Project: {solution_or_project}")
        self.logger.log(f"Configuration: {configuration}")
        self.logger.log(f"Platform: {platform}")
        if target:
            self.logger.log(f"Target: {target}")
        
        if dry_run:
            self.logger.log("[DRY RUN] Would build project")
            self.logger.log("=" * 70 + "\n")
            return True
        
        if not self.msbuild_path:
            self.logger.log("✗ MSBuild not found. Please install Visual Studio.", level="ERROR")
            self.logger.log("=" * 70 + "\n")
            return False
        
        try:
            cmd = [
                str(self.msbuild_path),
                str(solution_or_project),
                f"/p:Configuration={configuration}",
                f"/p:Platform={platform}",
                "/m",  # Multi-processor build
                "/v:minimal",  # Minimal verbosity
            ]
            
            if target:
                cmd.append(f"/t:{target}")
            
            self.logger.log(f"Running: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            self.logger.log_command(' '.join(cmd), result.stdout + result.stderr, result.returncode)
            
            if result.returncode == 0:
                self.logger.log("✓ Build successful")
                self.logger.log("=" * 70 + "\n")
                return True
            else:
                self.logger.log(f"✗ Build failed with code {result.returncode}", level="ERROR")
                self.logger.log("=" * 70 + "\n")
                return False
                
        except Exception as e:
            self.logger.log(f"✗ Build failed: {e}", level="ERROR")
            self.logger.log("=" * 70 + "\n")
            return False


class BinaryCollector:
    """Collects and deploys CEF binaries."""
    
    def __init__(self, logger: Logger):
        self.logger = logger
    
    def collect_binaries(self, cef_source_dir: Path, build_dir: Path, 
                        target_dir: Path, dry_run: bool = False) -> bool:
        """Collect all required binaries and deploy to target directory."""
        self.logger.log("=" * 70)
        self.logger.log("Collecting and Deploying Binaries")
        self.logger.log("=" * 70)
        
        collections = {
            "include": cef_source_dir / "include",
            "Release": cef_source_dir / "Release",
            "Resources": cef_source_dir / "Resources",
            "libcef_dll_wrapper": build_dir / "libcef_dll_wrapper" / "Release",
        }
        
        self.logger.log(f"Target Directory: {target_dir}")
        
        if dry_run:
            self.logger.log("[DRY RUN] Would collect and deploy:")
            for name, path in collections.items():
                self.logger.log(f"  - {name}: {path}")
            self.logger.log("=" * 70 + "\n")
            return True
        
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy include folder
            include_src = collections["include"]
            include_dst = target_dir / "include"
            if include_src.exists():
                if include_dst.exists():
                    shutil.rmtree(include_dst)
                shutil.copytree(include_src, include_dst)
                self.logger.log(f"✓ Copied include folder: {include_dst}")
            else:
                self.logger.log(f"⚠ Include folder not found: {include_src}")
            
            # Copy Release binaries
            release_src = collections["Release"]
            if release_src.exists():
                for item in release_src.iterdir():
                    dst = target_dir / item.name
                    if item.is_file():
                        shutil.copy2(item, dst)
                    else:
                        if dst.exists():
                            shutil.rmtree(dst)
                        shutil.copytree(item, dst)
                self.logger.log(f"✓ Copied Release binaries")
            else:
                self.logger.log(f"⚠ Release folder not found: {release_src}")
            
            # Copy Resources
            resources_src = collections["Resources"]
            if resources_src.exists():
                for item in resources_src.iterdir():
                    dst = target_dir / item.name
                    if item.is_file():
                        shutil.copy2(item, dst)
                    else:
                        if dst.exists():
                            shutil.rmtree(dst)
                        shutil.copytree(item, dst)
                self.logger.log(f"✓ Copied Resources")
            else:
                self.logger.log(f"⚠ Resources folder not found: {resources_src}")
            
            # Copy libcef_dll_wrapper.lib
            wrapper_src = collections["libcef_dll_wrapper"] / "libcef_dll_wrapper.lib"
            if wrapper_src.exists():
                wrapper_dst = target_dir / "libcef_dll_wrapper.lib"
                shutil.copy2(wrapper_src, wrapper_dst)
                self.logger.log(f"✓ Copied libcef_dll_wrapper.lib")
            else:
                self.logger.log(f"⚠ libcef_dll_wrapper.lib not found: {wrapper_src}")
            
            self.logger.log(f"\n✓ All binaries deployed to: {target_dir}")
            self.logger.log("=" * 70 + "\n")
            return True
            
        except Exception as e:
            self.logger.log(f"✗ Binary collection failed: {e}", level="ERROR")
            self.logger.log("=" * 70 + "\n")
            return False


class CEFBuildAgent:
    """Main agent orchestrating the CEF build process."""
    
    def __init__(self, args):
        self.args = args
        
        # Setup directories
        self.log_dir = Path(args.log_dir) / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.cmake_dir = Path("temp/cmake")
        self.cmake_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.logger = Logger(self.log_dir)
        self.cmake_downloader = CMakeDownloader(self.logger)
        self.cmake_configurator = None  # Will be initialized after CMake download
        self.vs_modifier = VSProjectModifier(self.logger)
        self.vs_builder = VSBuilder(self.logger)
        self.binary_collector = BinaryCollector(self.logger)
        
        # Results tracking
        self.results = {
            'cef_source': args.cef_source,
            'dry_run': args.dry_run,
            'status': 'pending'
        }
    
    def run(self):
        """Execute the build process."""
        self.logger.log("=" * 70)
        self.logger.log("CEF Build Agent - libcef_dll_wrapper Builder")
        self.logger.log("=" * 70)
        self.logger.log(f"CEF Source: {self.args.cef_source}")
        self.logger.log(f"Output Directory: {self.args.output_dir}")
        self.logger.log(f"Dry Run: {self.args.dry_run}")
        self.logger.log("=" * 70 + "\n")
        
        try:
            cef_source = Path(self.args.cef_source)
            if not cef_source.exists():
                self.logger.log(f"✗ CEF source directory not found: {cef_source}", level="ERROR")
                return 1
            
            # Step 1: Download CMake (if needed)
            if not self.args.cmake_path:
                cmake_archive = self.cmake_downloader.download_cmake(
                    self.args.cmake_version,
                    self.cmake_dir,
                    self.args.dry_run
                )
                
                if not cmake_archive:
                    self.logger.log("✗ Failed to download CMake", level="ERROR")
                    return 1
                
                cmake_exe = self.cmake_downloader.extract_cmake(
                    cmake_archive,
                    self.cmake_dir / "extracted",
                    self.args.dry_run
                )
                
                if not cmake_exe:
                    self.logger.log("✗ Failed to extract CMake", level="ERROR")
                    return 1
            else:
                cmake_exe = Path(self.args.cmake_path)
                if not cmake_exe.exists():
                    self.logger.log(f"✗ CMake not found at: {cmake_exe}", level="ERROR")
                    return 1
            
            self.cmake_configurator = CMakeConfigurator(self.logger, cmake_exe)
            
            # Step 2: Configure CMake
            build_dir = cef_source / "build"
            if not self.cmake_configurator.configure(
                cef_source,
                build_dir,
                self.args.vs_generator,
                self.args.platform,
                self.args.dry_run
            ):
                self.logger.log("✗ CMake configuration failed", level="ERROR")
                return 1
            
            # Step 3: Generate (automatic with configure)
            if not self.cmake_configurator.generate(build_dir, self.args.dry_run):
                self.logger.log("✗ CMake generation failed", level="ERROR")
                return 1
            
            # Step 4: Modify project properties
            wrapper_project = build_dir / "libcef_dll_wrapper" / "libcef_dll_wrapper.vcxproj"
            if not self.args.dry_run and not wrapper_project.exists():
                self.logger.log(f"⚠ Project file not found: {wrapper_project}")
                self.logger.log("Skipping property modification...")
            else:
                if not self.vs_modifier.modify_runtime_library(
                    wrapper_project,
                    "MultiThreadedDLL",
                    self.args.dry_run
                ):
                    self.logger.log("⚠ Failed to modify project properties (continuing anyway)")
            
            # Step 5: Build libcef_dll_wrapper
            if not self.vs_builder.build_project(
                build_dir / "cef.sln",
                "Release",
                self.args.platform,
                "libcef_dll_wrapper",
                self.args.dry_run
            ):
                self.logger.log("✗ Build failed", level="ERROR")
                return 1
            
            # Step 6: Collect and deploy binaries
            output_dir = Path(self.args.output_dir)
            if not self.binary_collector.collect_binaries(
                cef_source,
                build_dir,
                output_dir,
                self.args.dry_run
            ):
                self.logger.log("✗ Binary collection failed", level="ERROR")
                return 1
            
            # Success
            self.results['status'] = 'success'
            
            self.logger.log("=" * 70)
            self.logger.log("✓ CEF Build Agent Completed Successfully")
            self.logger.log(f"Output Directory: {output_dir}")
            self.logger.log(f"Logs: {self.log_dir}")
            self.logger.log("=" * 70)
            
            return 0
            
        except Exception as e:
            self.logger.log(f"✗ Fatal error: {e}", level="ERROR")
            self.results['status'] = 'error'
            return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="CEF Build Agent - Automated libcef_dll_wrapper Builder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build with auto-downloaded CMake
  python cef_build_agent.py --cef-source "C:\\cef_binary_140.1.13+g5eb3258+chromium-140.0.7339.41_windows64"
  
  # Build with existing CMake
  python cef_build_agent.py --cef-source "C:\\cef" --cmake-path "C:\\CMake\\bin\\cmake.exe"
  
  # Dry run to see what would happen
  python cef_build_agent.py --cef-source "C:\\cef" --dry-run
  
  # Custom output directory
  python cef_build_agent.py --cef-source "C:\\cef" --output-dir "D:\\bin\\NT\\cef\\release"
"""
    )
    
    parser.add_argument(
        "--cef-source",
        required=True,
        help="Path to extracted CEF source directory (e.g., cef_binary_140.1.13...)"
    )
    
    parser.add_argument(
        "--output-dir",
        default="bin/NT/cef/release",
        help="Directory to deploy built binaries (default: bin/NT/cef/release)"
    )
    
    parser.add_argument(
        "--cmake-path",
        help="Path to cmake executable (if not provided, will download automatically)"
    )
    
    parser.add_argument(
        "--cmake-version",
        default="3.30.1",
        help="CMake version to download if --cmake-path not provided (default: 3.30.1)"
    )
    
    parser.add_argument(
        "--vs-generator",
        help="Visual Studio generator (auto-detected if not provided)"
    )
    
    parser.add_argument(
        "--platform",
        default="x64",
        help="Build platform (default: x64)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the process without making changes"
    )
    
    parser.add_argument(
        "--log-dir",
        default="temp/cef-build-logs",
        help="Directory to store logs (default: temp/cef-build-logs)"
    )
    
    args = parser.parse_args()
    
    # Run the agent
    agent = CEFBuildAgent(args)
    exit_code = agent.run()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
