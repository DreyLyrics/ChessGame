# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['UI\\menu.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets'), ('DataBase', 'DataBase'), ('stockfish', 'stockfish'), ('src', 'src'), ('UI', 'UI'), ('Bot', 'Bot'), ('LocalBattle', 'LocalBattle'), ('Online', 'Online')],
    hiddenimports=['pygame', 'flask', 'flask_socketio', 'engineio', 'socketio', 'eventlet', 'tkinter', 'sqlite3', 'engineio.async_drivers.threading', 'socketio.async_drivers.threading'],
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
    name='ChessGamePlay',
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
    name='ChessGamePlay',
)
