"""
Online/server_config.py
Re-export SERVER_URL từ AppSeverConfig để OnMatch.py dùng.
"""
import os, sys
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from AppSeverConfig import SERVER_URL
