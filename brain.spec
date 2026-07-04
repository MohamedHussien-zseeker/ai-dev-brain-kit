# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['brain/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['brain.commands.consolidate', 'brain.commands.review', 'brain.commands.context', 'brain.commands.capture', 'brain.commands.doctor', 'brain.commands.hook', 'brain.commands.init', 'brain.provider', 'brain.config'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'PyQt5', 'PySide2', 'PySide6', 'matplotlib', 'numpy', 'pandas', 'PIL', 'cv2', 'scipy', 'yaml'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='brain',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
