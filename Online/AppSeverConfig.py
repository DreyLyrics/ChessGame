"""
Online/AppSeverConfig.py
Cấu hình tập trung — Railway WAN server + PostgreSQL.

Sau khi deploy Railway:
    Đổi RAILWAY_URL thành URL thật của bạn (nếu chưa set env var).
"""

import os

RAILWAY_URL = os.environ.get(
    'CHESS_SERVER_URL',
    'https://web-production-0f37b.up.railway.app'
).rstrip('/')

# Socket.IO server (game online, matchmaking)
SERVER_URL = RAILWAY_URL

# REST API server (database)
DB_API_URL = RAILWAY_URL + '/api'

# Timeout HTTP requests (giây)
REQUEST_TIMEOUT = 10
