# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('c:\\Users\\datla\\Desktop\\ChessGame\\assets', 'assets'), ('c:\\Users\\datla\\Desktop\\ChessGame\\DataBase', 'DataBase'), ('c:\\Users\\datla\\Desktop\\ChessGame\\stockfish', 'stockfish'), ('c:\\Users\\datla\\Desktop\\ChessGame\\src', 'src'), ('c:\\Users\\datla\\Desktop\\ChessGame\\UI', 'UI'), ('c:\\Users\\datla\\Desktop\\ChessGame\\Bot', 'Bot'), ('c:\\Users\\datla\\Desktop\\ChessGame\\LocalBattle', 'LocalBattle'), ('c:\\Users\\datla\\Desktop\\ChessGame\\Online', 'Online')]
binaries = []
hiddenimports = ['pygame', 'pygame.mixer', 'pygame.font', 'pygame.image', 'flask', 'flask_socketio', 'engineio', 'engineio.async_drivers', 'engineio.async_drivers.threading', 'socketio', 'socketio.exceptions', 'eventlet', 'eventlet.hubs', 'eventlet.hubs.epolls', 'eventlet.hubs.kqueue', 'eventlet.hubs.selects', 'eventlet.support', 'dns', 'dns.resolver', 'tkinter', 'tkinter.filedialog', 'sqlite3', 'hashlib', 'threading', 'copy', 'math', 'collections']
tmp_ret = collect_all('flask_socketio')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('engineio')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('socketio')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('eventlet')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['c:\\Users\\datla\\Desktop\\ChessGame\\UI\\menu.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['c:\\Users\\datla\\Desktop\\ChessGame\\App\\runtime_hook.py'],
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
