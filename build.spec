# -*- mode: python ; coding: utf-8 -*-
"""
VRChat Discord Uploader - PyInstaller ビルド設定
"""

import sys
from pathlib import Path

block_cipher = None

# プロジェクトルート
project_root = Path('.').resolve()

a = Analysis(
    ['main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        ('src/assets/icon.ico', 'src/assets'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtWidgets',
        'PyQt6.QtGui',
        'PIL',
        'PIL.Image',
        'watchdog',
        'watchdog.observers',
        'watchdog.events',
        'requests',
        'cryptography',
        'cryptography.fernet',
        'loguru',
        'sqlite3',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'PyQt6.QtNetwork',
        'PyQt6.QtSql',
        'PyQt6.QtWebEngine',
        'PyQt6.QtWebEngineCore',
        'PyQt6.QtWebEngineWidgets',
        'PyQt6.QtQml',
        'PyQt6.QtQuick',
        'PyQt6.QtQuickWidgets',
        'PyQt6.QtTest',
        'PyQt6.QtOpenGL',
        'PyQt6.QtOpenGLWidgets',
        'PyQt6.QtMultimedia',
        'PyQt6.QtMultimediaWidgets',
        'PyQt6.QtBluetooth',
        'PyQt6.QtPositioning',
        'PyQt6.QtSensors',
        'PyQt6.QtWebSockets',
        'PyQt6.QtXml',
        'PyQt6.QtSvg',
        'PyQt6.QtPrintSupport',
        'PyQt6.QtDBus',
        'PyQt6.QtDesigner',
        'PyQt6.QtHelp',
        'PyQt6.QtLocation',
        'PyQt6.QtNfc',
        'PyQt6.QtPdf',
        'PyQt6.QtPdfWidgets',
        'PyQt6.QtQuick3D',
        'PyQt6.QtRemoteObjects',
        'PyQt6.QtSerialPort',
        'PyQt6.QtTextToSpeech',
        'PyQt6.QtWebChannel',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='VRChatDiscordUploader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUIアプリなのでコンソールを非表示
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='src/assets/icon.ico',
)
