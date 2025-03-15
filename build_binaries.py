#!/usr/bin/env python3
"""Build standalone executables for Impulse Check"""

import os
import platform
import subprocess
import shutil
from pathlib import Path

def build_executable():
    """Build standalone executable using PyInstaller"""
    system = platform.system().lower()
    print(f"Building for {system}...")
    
    # Clean dist directory if it exists
    dist_dir = Path("dist")
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    
    # Create output directory
    output_dir = Path("dist") / system
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Build the executable
    cmd = [
        "pyinstaller",
        "--onefile",
        "--clean",
        "--name", f"impulse-check-{system}",
        "main.py"
    ]
    
    if system == "windows":
        # Add icon for Windows
        cmd.extend(["--icon", "icon.ico"])
    elif system == "darwin":  # macOS
        cmd.extend(["--windowed"])  # Creates a .app on macOS
    
    subprocess.run(cmd, check=True)
    
    # Move the executable to the output directory
    if system == "darwin":
        app_path = Path("dist") / "impulse-check-darwin.app"
        if app_path.exists():
            shutil.move(str(app_path), str(output_dir))
    else:
        exe_name = "impulse-check-windows.exe" if system == "windows" else f"impulse-check-{system}"
        exe_path = Path("dist") / exe_name
        if exe_path.exists():
            shutil.move(str(exe_path), str(output_dir))
    
    print(f"Build complete! Executable saved to {output_dir}")

if __name__ == "__main__":
    build_executable()
