"""
AppSeverConfig.py
Cấu hình tập trung cho toàn bộ ứng dụng khi chạy qua mạng WAN.

Cách dùng:
    from AppSeverConfig import SERVER_URL, DB_API_URL, USE_REMOTE_DB

Sau khi deploy Railway:
    1. Đổi RAILWAY_URL thành URL thật của bạn
    2. Tất cả module khác import từ file này — chỉ cần đổi 1 chỗ
"""

import os

# ── URL Railway server ────────────────────────────────────────────────────────
# Đổi thành URL Railway của bạn
RAILWAY_URL = os.environ.get(
    'CHESS_SERVER_URL',
    'https://web-production-0f37b.up.railway.app'
).rstrip('/')

# Socket.IO server (game online, matchmaking)
SERVER_URL  = RAILWAY_URL

# REST API server (database: login, register, profile, history)
DB_API_URL  = RAILWAY_URL + '/api'

# Bật/tắt remote database
# True  → dùng server Railway (WAN, nhiều máy dùng chung 1 DB)
# False → dùng SQLite local (offline)
USE_REMOTE_DB = True

# Timeout cho HTTP requests (giây)
REQUEST_TIMEOUT = 10
