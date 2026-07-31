"""
Automated PyInstaller Executable Build & Packaging Script for BTIS3053 Project.
Packages application into standalone Windows directory and ZIP bundle for 1-click execution.
"""
import os
import sys
import shutil
import subprocess
import zipfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = BASE_DIR / "dist"
BUILD_DIR = BASE_DIR / "build"
APP_DIST_DIR = DIST_DIR / "AI_Video_Editor"

def check_pyinstaller():
    """Ensure PyInstaller is available."""
    try:
        import PyInstaller
        print("[BUILD] PyInstaller module detected.")
        return True
    except ImportError:
        print("[BUILD] Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        return True

def run_build():
    """Run PyInstaller build process."""
    print("=== BTIS3053 Windows Standalone Executable Build ===")
    check_pyinstaller()

    spec_file = BASE_DIR / "ai_editor.spec"
    if not spec_file.exists():
        print(f"[ERROR] Spec file missing: {spec_file}")
        sys.exit(1)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        str(spec_file)
    ]
    print(f"[BUILD] Executing command: {' '.join(cmd)}")
    subprocess.check_call(cmd, cwd=str(BASE_DIR))

    # Copy required runtime folders (videos, edl, output) into dist bundle
    for folder_name in ["videos", "edl", "output"]:
        target_folder = APP_DIST_DIR / folder_name
        target_folder.mkdir(parents=True, exist_ok=True)
        source_folder = BASE_DIR / folder_name
        if source_folder.exists():
            for item in source_folder.glob("*"):
                if item.is_file():
                    shutil.copy(item, target_folder / item.name)

    print(f"[SUCCESS] Standalone app bundle created at: {APP_DIST_DIR}")

    # Create distributable ZIP archive
    zip_path = DIST_DIR / "BTIS3053_AI_Video_Editor_Windows.zip"
    print(f"[PACKAGING] Creating ZIP archive: {zip_path}...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(APP_DIST_DIR):
            for file in files:
                abs_file = Path(root) / file
                rel_path = abs_file.relative_to(DIST_DIR)
                zipf.write(abs_file, rel_path)

    print(f"=== BUILD COMPLETED SUCCESSFULLY! Distributable ZIP: {zip_path} ===")

if __name__ == "__main__":
    run_build()
