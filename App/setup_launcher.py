"""
App/setup_launcher.py
Tao setup.exe -- khi chay se tu dong chay App/setup.py de build ChessGamePlay.exe

Chay:
    python App/setup_launcher.py

Ket qua:
    App/setup.exe
"""

import subprocess
import sys
import os
import shutil

ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY      = sys.executable
SETUP   = os.path.join(ROOT, 'App', 'setup.py')
OUT_DIR = os.path.join(ROOT, 'App')
WORK    = os.path.join(ROOT, 'App', 'launcher_tmp')
NAME    = 'setup'

def sep(c='=', n=50):
    print(c * n)

sep()
print('  Tao setup.exe')
sep()

# Kiem tra PyInstaller
r = subprocess.run(f'"{PY}" -m PyInstaller --version',
                   shell=True, capture_output=True)
if r.returncode != 0:
    print('[*] Cai PyInstaller...')
    subprocess.run(f'"{PY}" -m pip install pyinstaller', shell=True)

# Tao wrapper script -- setup.exe se chay setup.py bang Python
WRAPPER = os.path.join(ROOT, 'App', '_setup_wrapper.py')
wrapper_code = f'''
import subprocess
import sys
import os

# Tim Python
PY = sys.executable

# Tim setup.py cung thu muc voi setup.exe
HERE   = os.path.dirname(os.path.abspath(__file__))
SETUP  = os.path.join(HERE, "setup.py")

if not os.path.isfile(SETUP):
    import tkinter.messagebox as mb
    mb.showerror("Loi", f"Khong tim thay setup.py\\n{{SETUP}}")
    sys.exit(1)

# Chay setup.py trong cua so console
subprocess.run([PY, SETUP], cwd=HERE)
input("\\nNhan Enter de dong...")
'''

with open(WRAPPER, 'w', encoding='utf-8') as f:
    f.write(wrapper_code)

# Build setup.exe
cmd = (
    f'"{PY}" -m PyInstaller'
    f' --noconfirm'
    f' --onefile'
    f' --console'                          # hien console de xem tien trinh build
    f' --name "{NAME}"'
    f' --distpath "{OUT_DIR}"'
    f' --workpath "{WORK}"'
    f' --specpath "{OUT_DIR}"'
    f' --add-data "{SETUP}{os.pathsep}."'  # copy setup.py vao cung thu muc exe
    f' "{WRAPPER}"'
)

print(f'\n[*] Dang tao setup.exe...')
result = subprocess.run(cmd, shell=True)

# Don dep
for p in [WORK, WRAPPER,
          os.path.join(OUT_DIR, f'{NAME}.spec')]:
    if os.path.isdir(p):
        shutil.rmtree(p, ignore_errors=True)
    elif os.path.isfile(p):
        os.remove(p)

if result.returncode == 0:
    sep()
    print(f'  THANH CONG!')
    print(f'  Output: {OUT_DIR}\\{NAME}.exe')
    sep()
else:
    print('\n[X] That bai! Xem log o tren.')
    sys.exit(1)
