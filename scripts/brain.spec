# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for brain CLI — Linux and Windows builds."""

import platform
from pathlib import Path

block_cipher = None

HERE = Path(__file__).resolve().parent.parent

HIDDEN_IMPORTS = [
    "brain.commands.consolidate",
    "brain.commands.review",
    "brain.commands.context",
    "brain.commands.capture",
    "brain.commands.doctor",
    "brain.commands.hook",
    "brain.commands.init",
    "brain.provider",
    "brain.config",
]

EXCLUDES = [
    "tkinter",
    "PyQt5",
    "PySide2",
    "PySide6",
    "matplotlib",
    "numpy",
    "pandas",
    "PIL",
    "cv2",
    "scipy",
    "yaml",
]

a = Analysis(
    [str(HERE / "brain" / "__main__.py")],
    pathex=[str(HERE)],
    binaries=[],
    datas=[],
    hiddenimports=HIDDEN_IMPORTS,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="brain",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    contents_directory="brain-app",
)

if platform.system() == "Windows":
    COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name="brain",
    )
