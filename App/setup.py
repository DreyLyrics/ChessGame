"""
App/setup.py
Build script dung PyInstaller -- dong goi ChessGamePlay thanh .exe

Chay:
    python App/setup.py
"""

import subprocess
import sys
import os
import shutil

ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY    = sys.executable
ENTRY = os.path.join(ROOT, 'UI', 'menu.py')
DIST  = os.path.join(os.path.expanduser('~'), 'Desktop', NAME if 'NAME' in dir() else 'ChessGamePlay')
WORK  = os.path.join(ROOT, 'App', 'build_tmp')
HOOK  = os.path.join(ROOT, 'App', 'runtime_hook.py')
NAME  = 'ChessGamePlay'
DIST  = os.path.join(os.path.expanduser('~'), 'Desktop', NAME)
SEP   = os.pathsep

def sep(c='=', n=54):
    print(c * n)

def run(cmd):
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f'\n[X] Lenh that bai!')
        sys.exit(1)

sep()
print('  ChessGamePlay -- Build EXE')
sep()

# ── Kiem tra va cai thu vien ──────────────────────────────────────────────────
print('\n[*] Kiem tra PyInstaller...')
r = subprocess.run(f'"{PY}" -m PyInstaller --version',
                   shell=True, capture_output=True)
if r.returncode != 0:
    print('[*] Cai PyInstaller...')
    run(f'"{PY}" -m pip install pyinstaller')

print('[*] Kiem tra thu vien...')
run(f'"{PY}" -m pip install pygame flask flask-socketio eventlet '
    f'python-engineio python-socketio --quiet')

# ── Tao runtime hook ──────────────────────────────────────────────────────────
hook_code = r'''
import sys
import os

if hasattr(sys, '_MEIPASS'):
    BASE = sys._MEIPASS
else:
    BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Them tat ca thu muc vao sys.path
for folder in ['src', 'UI', 'Bot', 'LocalBattle', 'Online', 'DataBase']:
    p = os.path.join(BASE, folder)
    if p not in sys.path:
        sys.path.insert(0, p)

# Duong dan database va root
os.environ['CHESS_DB_DIR'] = os.path.join(BASE, 'DataBase')
os.environ['CHESS_ROOT']   = BASE

# Fix duong dan assets khi chay tu exe
os.chdir(BASE)
'''

with open(HOOK, 'w', encoding='utf-8') as f:
    f.write(hook_code)
print('[*] Da tao runtime_hook.py')

# ── add-data ──────────────────────────────────────────────────────────────────
def add(src_rel, dst):
    src = os.path.join(ROOT, src_rel)
    if not os.path.exists(src):
        print(f'[!] Canh bao: khong tim thay {src}')
    return f'--add-data "{src}{SEP}{dst}"'

add_data = ' '.join([
    add('assets',      'assets'),
    add('DataBase',    'DataBase'),
    add('stockfish',   'stockfish'),
    add('src',         'src'),
    add('UI',          'UI'),
    add('Bot',         'Bot'),
    add('LocalBattle', 'LocalBattle'),
    add('Online',      'Online'),
])

# ── hidden imports ────────────────────────────────────────────────────────────
hidden = ' '.join([
    '--hidden-import pygame',
    '--hidden-import pygame.mixer',
    '--hidden-import pygame.font',
    '--hidden-import pygame.image',
    '--hidden-import flask',
    '--hidden-import flask_socketio',
    '--hidden-import engineio',
    '--hidden-import engineio.async_drivers',
    '--hidden-import engineio.async_drivers.threading',
    '--hidden-import socketio',
    '--hidden-import socketio.exceptions',
    '--hidden-import eventlet',
    '--hidden-import eventlet.hubs',
    '--hidden-import eventlet.hubs.epolls',
    '--hidden-import eventlet.hubs.kqueue',
    '--hidden-import eventlet.hubs.selects',
    '--hidden-import eventlet.support',
    '--hidden-import dns',
    '--hidden-import dns.resolver',
    '--hidden-import tkinter',
    '--hidden-import tkinter.filedialog',
    '--hidden-import sqlite3',
    '--hidden-import hashlib',
    '--hidden-import threading',
    '--hidden-import copy',
    '--hidden-import math',
    '--hidden-import collections',
])

# ── collect-all (dam bao lay du data cua package) ────────────────────────────
collect = ' '.join([
    '--collect-all flask_socketio',
    '--collect-all engineio',
    '--collect-all socketio',
    '--collect-all eventlet',
])

# ── lenh PyInstaller ──────────────────────────────────────────────────────────
cmd = (
    f'"{PY}" -m PyInstaller'
    f' --noconfirm'
    f' --onedir'
    f' --windowed'
    f' --name "{NAME}"'
    f' --distpath "{DIST}"'
    f' --workpath "{WORK}"'
    f' --specpath "{os.path.join(ROOT, "App")}"'
    f' --runtime-hook "{HOOK}"'
    f' {add_data}'
    f' {hidden}'
    f' {collect}'
    f' "{ENTRY}"'
)

print(f'\n[*] Bat dau build...')
print(f'    Entry : {ENTRY}')
print(f'    Output: {DIST}\\{NAME}\n')

run(cmd)

# ── Copy stockfish exe vao dist ──────────────────────────────────────────────
sf_src = os.path.join(ROOT, 'stockfish', 'stockfish-windows-x86-64-avx2.exe')
sf_dst_dir = os.path.join(DIST, NAME, 'stockfish')
os.makedirs(sf_dst_dir, exist_ok=True)
if os.path.isfile(sf_src):
    shutil.copy2(sf_src, os.path.join(sf_dst_dir, 'stockfish-windows-x86-64-avx2.exe'))
    print(f'[*] Da copy stockfish.exe -> {sf_dst_dir}')

# ── Don dep ───────────────────────────────────────────────────────────────────
for p in [WORK, HOOK]:
    if os.path.isdir(p):
        shutil.rmtree(p, ignore_errors=True)
    elif os.path.isfile(p):
        os.remove(p)

sep()
print(f'  BUILD THANH CONG!')
print(f'  Output : {DIST}\\{NAME}\\{NAME}.exe')
sep()
