"""
Online/server_config.py — Re-export SERVER_URL từ AppSeverConfig.
"""
import os, sys
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from AppSeverConfig import SERVER_URL
