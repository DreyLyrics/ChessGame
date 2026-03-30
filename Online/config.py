"""
Online/config.py
Cấu hình server URL cho chế độ online.

Sau khi deploy lên Railway/Render:
  1. Copy URL từ dashboard (vd: https://chess-server-xxx.railway.app)
  2. Paste vào SERVER_URL bên dưới
  3. Xóa dòng fallback localhost nếu không cần test local
"""

# ── Đổi URL này sau khi deploy ────────────────────────────────────────────────
SERVER_URL = 'https://YOUR-APP.railway.app'

# Fallback khi chạy local (để test không cần deploy)
import os
if os.environ.get('CHESS_SERVER_URL'):
    SERVER_URL = os.environ['CHESS_SERVER_URL']
elif SERVER_URL == 'https://YOUR-APP.railway.app':
    # Chưa cấu hình → dùng localhost
    SERVER_URL = 'http://localhost:5000'
