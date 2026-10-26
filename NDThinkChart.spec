# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config/theme.qss', 'config'),
        # Vendored Lightweight Charts v5.2.1 tree (P6-T12 / AC-D47.6, AC-D47.8):
        # shipped whole so the offline page (chart.html) and every relative
        # asset it loads resolve inside the bundle via ndt://lwc/. The version
        # pin travels with it (chart_assets/lwc/VERSION + ATTRIBUTION.md).
        ('chart_assets/lwc', 'chart_assets/lwc'),
    ],
    hiddenimports=[
        # QtWebEngine host + QWebChannel bridge (ui/lwc_host.py, ui/lwc_bridge.py).
        # Import-guarded in code (DG88); naming them here keeps PyInstaller from
        # pruning the modules (and the Chromium runtime they pull) from the app.
        'PyQt6.QtWebEngineCore',
        'PyQt6.QtWebEngineWidgets',
        'PyQt6.QtWebChannel',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='NDThinkChart',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NDThinkChart',
)
app = BUNDLE(
    coll,
    name='NDThinkChart.app',
    icon=None,
    bundle_identifier='com.ndthinkchart.app',
)
