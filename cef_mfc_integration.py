#!/usr/bin/env python3
"""
CEF MFC Integration Module

Handles integration with MFC GUI applications:
- Deploys CEF binaries to MFC GUI binary directory
- Builds MFC GUI solution
- Replaces binaries
- Provides testing instructions

This module extends the CEF Unified Agent with MFC-specific deployment.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import json


class MFCIntegration:
    """Handles MFC GUI integration and deployment."""
    
    def __init__(self, logger, config: Dict):
        self.logger = logger
        self.config = config
        
        # MFC-specific paths from config
        self.mfc_solution_path = Path(config.get('mfc_solution_path', ''))
        self.mfc_binary_dir = Path(config.get('mfc_binary_dir', ''))
        self.mfc_cef_binary_dir = Path(config.get('mfc_cef_binary_dir', ''))
        
    def validate_paths(self) -> bool:
        """Validate MFC integration paths."""
        self.logger.log("=" * 70)
        self.logger.log("MFC Integration - Path Validation")
        self.logger.log("=" * 70)
        
        if not self.mfc_solution_path:
            self.logger.log("⚠ MFC solution path not configured")
            self.logger.log("  Set 'mfc_solution_path' in config to enable MFC integration")
            return False
        
        if not self.mfc_binary_dir:
            self.logger.log("⚠ MFC binary directory not configured")
            self.logger.log("  Set 'mfc_binary_dir' in config")
            return False
        
        # Check if solution exists
        if not self.mfc_solution_path.exists():
            self.logger.log(f"✗ MFC solution not found: {self.mfc_solution_path}", level="ERROR")
            return False
        
        self.logger.log(f"✓ MFC Solution: {self.mfc_solution_path}")
        self.logger.log(f"✓ MFC Binary Dir: {self.mfc_binary_dir}")
        self.logger.log(f"✓ MFC CEF Binary Dir: {self.mfc_cef_binary_dir}")
        self.logger.log("=" * 70 + "\n")
        
        return True
    
    def build_mfc_solution(self, configuration: str = "Release", platform: str = "x64", 
                          dry_run: bool = False) -> bool:
        """Build MFC GUI solution."""
        self.logger.log("=" * 70)
        self.logger.log("Building MFC GUI Solution")
        self.logger.log("=" * 70)
        self.logger.log(f"Solution: {self.mfc_solution_path}")
        self.logger.log(f"Configuration: {configuration}")
        self.logger.log(f"Platform: {platform}")
        
        if dry_run:
            self.logger.log("[DRY RUN] Would build MFC solution")
            self.logger.log("=" * 70 + "\n")
            return True
        
        # Find MSBuild
        msbuild_path = self._find_msbuild()
        if not msbuild_path:
            self.logger.log("✗ MSBuild not found", level="ERROR")
            return False
        
        try:
            cmd = [
                str(msbuild_path),
                str(self.mfc_solution_path),
                f"/p:Configuration={configuration}",
                f"/p:Platform={platform}",
                "/m",  # Multi-processor build
                "/v:minimal",
            ]
            
            self.logger.log(f"Running: {' '.join(cmd)}\n")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.log("✓ MFC solution built successfully")
                self.logger.log("=" * 70 + "\n")
                return True
            else:
                self.logger.log(f"✗ Build failed with code {result.returncode}", level="ERROR")
                self.logger.log(f"Error output:\n{result.stderr}")
                self.logger.log("=" * 70 + "\n")
                return False
                
        except Exception as e:
            self.logger.log(f"✗ Build failed: {e}", level="ERROR")
            self.logger.log("=" * 70 + "\n")
            return False
    
    def deploy_cef_binaries(self, cef_output_dir: Path, dry_run: bool = False) -> bool:
        """Deploy CEF binaries to MFC binary directories."""
        self.logger.log("=" * 70)
        self.logger.log("Deploying CEF Binaries to MFC Application")
        self.logger.log("=" * 70)
        self.logger.log(f"Source: {cef_output_dir}")
        self.logger.log(f"MFC Binary Dir: {self.mfc_binary_dir}")
        self.logger.log(f"MFC CEF Binary Dir: {self.mfc_cef_binary_dir}")
        
        if dry_run:
            self.logger.log("[DRY RUN] Would deploy CEF binaries to MFC directories")
            self.logger.log("=" * 70 + "\n")
            return True
        
        try:
            # Create target directories if they don't exist
            self.mfc_binary_dir.mkdir(parents=True, exist_ok=True)
            if self.mfc_cef_binary_dir:
                self.mfc_cef_binary_dir.mkdir(parents=True, exist_ok=True)
            
            # Deploy to MFC CEF binary directory (bin\NT\cef\release\x64)
            if self.mfc_cef_binary_dir:
                self._copy_directory_contents(cef_output_dir, self.mfc_cef_binary_dir)
                self.logger.log(f"✓ Deployed to MFC CEF directory: {self.mfc_cef_binary_dir}")
            
            # Also copy CEF runtime DLLs to main MFC binary directory
            self._copy_cef_runtime_files(cef_output_dir, self.mfc_binary_dir)
            self.logger.log(f"✓ Deployed CEF runtime to MFC binary directory: {self.mfc_binary_dir}")
            
            self.logger.log("=" * 70 + "\n")
            return True
            
        except Exception as e:
            self.logger.log(f"✗ Deployment failed: {e}", level="ERROR")
            self.logger.log("=" * 70 + "\n")
            return False
    
    def _copy_directory_contents(self, src: Path, dst: Path):
        """Copy all contents from source to destination."""
        for item in src.iterdir():
            dst_item = dst / item.name
            if item.is_file():
                shutil.copy2(item, dst_item)
            elif item.is_dir():
                if dst_item.exists():
                    shutil.rmtree(dst_item)
                shutil.copytree(item, dst_item)
    
    def _copy_cef_runtime_files(self, src: Path, dst: Path):
        """Copy CEF runtime DLLs and resources to MFC binary directory."""
        # Files that need to be in the same directory as the MFC executable
        runtime_files = [
            'libcef.dll',
            'chrome_elf.dll',
            'd3dcompiler_47.dll',
            'libEGL.dll',
            'libGLESv2.dll',
            'vk_swiftshader.dll',
            'vulkan-1.dll',
        ]
        
        for filename in runtime_files:
            src_file = src / filename
            if src_file.exists():
                shutil.copy2(src_file, dst / filename)
        
        # Copy resource files
        resource_files = ['cef.pak', 'cef_100_percent.pak', 'cef_200_percent.pak', 
                         'cef_extensions.pak', 'devtools_resources.pak', 'icudtl.dat']
        
        for filename in resource_files:
            src_file = src / filename
            if src_file.exists():
                shutil.copy2(src_file, dst / filename)
        
        # Copy locales directory
        src_locales = src / 'locales'
        if src_locales.exists():
            dst_locales = dst / 'locales'
            if dst_locales.exists():
                shutil.rmtree(dst_locales)
            shutil.copytree(src_locales, dst_locales)
    
    def _find_msbuild(self) -> Optional[Path]:
        """Find MSBuild executable."""
        try:
            vswhere_path = Path(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")) / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"
            if vswhere_path.exists():
                result = subprocess.run(
                    [str(vswhere_path), "-latest", "-requires", "Microsoft.Component.MSBuild", 
                     "-find", "MSBuild\\**\\Bin\\MSBuild.exe"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0 and result.stdout.strip():
                    msbuild = Path(result.stdout.strip().split('\n')[0])
                    if msbuild.exists():
                        return msbuild
        except:
            pass
        
        return None
    
    def generate_test_instructions(self, output_path: Path):
        """Generate testing instructions document."""
        instructions = f"""# MFC GUI Testing Instructions

## Post-Build Verification

After CEF binaries have been deployed, follow these steps to test the MFC GUI application:

### 1. Verify Binary Deployment

Check that CEF binaries are present in:

**MFC CEF Binary Directory**: `{self.mfc_cef_binary_dir}`
- ✓ libcef.dll
- ✓ libcef_dll_wrapper.lib
- ✓ chrome_elf.dll
- ✓ *.pak files
- ✓ locales/ directory

**MFC Binary Directory**: `{self.mfc_binary_dir}`
- ✓ libcef.dll (runtime)
- ✓ chrome_elf.dll
- ✓ Other CEF runtime DLLs
- ✓ Resource files (*.pak)
- ✓ locales/ directory

### 2. Build MFC GUI Solution

The MFC solution has been built automatically:
- Solution: `{self.mfc_solution_path}`
- Configuration: Release
- Platform: x64

### 3. Launch MFC UI

1. Navigate to: `{self.mfc_binary_dir}`
2. Launch the MFC GUI executable
3. Verify the application starts without errors

### 4. Test in Home Context

Perform the following tests:

#### Basic Functionality
- [ ] Application launches successfully
- [ ] CEF browser control loads
- [ ] No error dialogs appear
- [ ] Application UI is responsive

#### CEF Integration
- [ ] Web pages load correctly
- [ ] JavaScript execution works
- [ ] Browser navigation functions
- [ ] No console errors

#### Performance
- [ ] Application startup time is acceptable
- [ ] Memory usage is normal
- [ ] No crashes or hangs
- [ ] Smooth UI interactions

### 5. Check Logs

Review application logs for:
- CEF initialization messages
- Any error or warning messages
- Performance metrics

### 6. Regression Testing

Test all major features:
- [ ] Feature 1: [Add your features]
- [ ] Feature 2: [Add your features]
- [ ] Feature 3: [Add your features]

### 7. Report Issues

If any issues are found:
1. Note the exact steps to reproduce
2. Capture error messages or logs
3. Check CEF version compatibility
4. Review deployment paths

## Rollback Procedure

If issues occur, rollback to previous CEF version:

1. Restore backup from: `temp/cef-agent-backups/`
2. Rebuild MFC solution
3. Redeploy binaries
4. Retest

## Success Criteria

✓ All tests pass
✓ No errors in logs
✓ Application performs as expected
✓ CEF integration works correctly

---

**CEF Version**: {self.config.get('cef_version', 'N/A')}
**Build Date**: {Path(output_path).stat().st_mtime if output_path.exists() else 'N/A'}
**Configuration**: Release x64
"""
        
        test_instructions_path = output_path.parent / "MFC_TEST_INSTRUCTIONS.md"
        test_instructions_path.write_text(instructions, encoding='utf-8')
        
        self.logger.log(f"✓ Test instructions generated: {test_instructions_path}")
        return test_instructions_path


def integrate_with_mfc(unified_agent, dry_run: bool = False) -> bool:
    """
    Integrate CEF build output with MFC GUI application.
    
    This function should be called after the unified agent completes.
    """
    logger = unified_agent.logger
    config = unified_agent.config.config
    
    # Check if MFC integration is enabled
    if not config.get('enable_mfc_integration', False):
        logger.log("⊘ MFC integration disabled in configuration")
        return True
    
    logger.log("\n" + "=" * 70)
    logger.log("PHASE 3: MFC GUI INTEGRATION")
    logger.log("=" * 70 + "\n")
    
    # Initialize MFC integration
    mfc = MFCIntegration(logger, config)
    
    # Validate paths
    if not mfc.validate_paths():
        logger.log("⚠ MFC integration skipped (paths not configured)")
        return True
    
    # Build MFC solution
    if not mfc.build_mfc_solution(
        config.get('build_configuration', 'Release'),
        config.get('architecture', 'x64'),
        dry_run
    ):
        logger.log("✗ MFC solution build failed", level="ERROR")
        return False
    
    # Deploy CEF binaries
    cef_output_dir = Path(config.get('output_directory', 'bin/NT/cef/release'))
    if not mfc.deploy_cef_binaries(cef_output_dir, dry_run):
        logger.log("✗ CEF binary deployment failed", level="ERROR")
        return False
    
    # Generate test instructions
    if not dry_run:
        mfc.generate_test_instructions(cef_output_dir)
    
    logger.log("\n" + "=" * 70)
    logger.log("✓ MFC INTEGRATION COMPLETED")
    logger.log("=" * 70)
    logger.log("\nNext Steps:")
    logger.log("  1. Review MFC_TEST_INSTRUCTIONS.md")
    logger.log("  2. Launch MFC GUI application")
    logger.log("  3. Test in Home context")
    logger.log("  4. Verify all functionality")
    logger.log("=" * 70 + "\n")
    
    return True


if __name__ == "__main__":
    print("This module should be imported and used with cef_unified_agent.py")
    print("\nTo enable MFC integration, add to cef_config.json:")
    print("""
{
  "enable_mfc_integration": true,
  "mfc_solution_path": "path/to/your/solution.sln",
  "mfc_binary_dir": "path/to/mfc/bin",
  "mfc_cef_binary_dir": "path/to/mfc/bin/NT/cef/release/x64"
}
""")
