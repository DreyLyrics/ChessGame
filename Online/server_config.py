"""
Online/server_config.py
URL server Railway cho chế độ online.
"""

import os

SERVER_URL = os.environ.get(
    'CHESS_SERVER_URL',
    'https://web-production-0f37b.up.railway.app'
)
