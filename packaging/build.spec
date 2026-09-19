# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller build specification for NDThinkChart.

Bundles the application into a macOS .app package with:
- Windowed mode (no terminal)
- Application name: NDThinkChart
- macOS bundle identifier: com.ndthinkchart.app
- ARM64 target (Apple Silicon)
- QSS theme and sound assets included
"""

import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Detect if we're building on macOS (arm64)
is_darwin = sys.platform == "darwin"

# ── Paths ──────────────────────────────────────────────────────────────
# PyInstaller executes spec files without __file__; cwd is the project root.
_spec_dir = Path(os.getcwd()) / "packaging"
_project_root = _spec_dir.parent
_config_dir = _project_root / "config"
_data_dir = _project_root / "data"
_sound_dir = _project_root / "assets" / "sounds" if (_project_root / "assets" / "sounds").exists() else None

# ── Analysis ───────────────────────────────────────────────────────────
a = Analysis(
    [str(_project_root / "main.py")],  # Entry point
    pathex=[str(_project_root)],
    binaries=[],
    datas=[
        # Bundle QSS theme
        (str(_config_dir / "theme.qss"), "config"),
    ],
    hiddenimports=[
        "PyQt6",
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        "pyqtgraph",
        "ibapi",
        "ibapi.client",
        "ibapi.wrapper",
        "ibapi.contract",
        "ibapi.order",
        "ibapi.orderCondition",
        "ibapi.ticktype",
        "sqlite3",
        "numpy",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "PyQt5",
        "PySide2",
        "PySide6",
        "tkinter",
        "test",
        "pytest",
        "torch",
        "tensorflow",
        "matplotlib",
        "scipy",
        "sklearn",
        "pandas",
        "onnxruntime",
        "transformers",
        "pytz",
        "cv2",
        "urllib3",
        "mutagen",
        "brotli",
        "certifi",
        "secretstorage",
        "curl_cffi",
    ],
    noarchive=False,
)
a.onefile = False  # Force onedir mode for macOS .app bundles

# ── Sound assets (if available) ────────────────────────────────────────
if _sound_dir and _sound_dir.exists():
    for sound_file in _sound_dir.rglob("*"):
        if sound_file.is_file():
            a.datas.append((str(sound_file), "assets/sounds"))

# ── PyInstaller executable ─────────────────────────────────────────────
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# macOS-specific options: build as .app bundle
if is_darwin:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name="NDThinkChart",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,  # windowed mode
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch="arm64",
        codesign_identity=None,
        entitlements=None,
    )
    app = BUNDLE(
        exe,
        name="NDThinkChart",
        icon=None,
        bundle_identifier="com.ndthinkchart.app",
        info_plist={
            "CFBundleName": "NDThinkChart",
            "CFBundleDisplayName": "NDThinkChart",
            "CFBundleIdentifier": "com.ndthinkchart.app",
            "CFBundleVersion": "1.0.0",
            "CFBundleShortVersionString": "1.0.0",
            "NSHighResolutionCapable": True,
            "NSRequiresAquaWindowStyles": False,
            "LSMinimumSystemVersion": "11.0",
        },
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name="NDThinkChart",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements=None,
    )