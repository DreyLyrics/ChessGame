"""
DataBase/db.py — ChessGamePlay database
Chỉ dùng PostgreSQL (psycopg3).
DATABASE_URL được inject tự động bởi Railway.
"""

import os
import hashlib
import psycopg

# Load .env file nếu có
def _load_env():
    for base in (os.path.dirname(os.path.abspath(__file__)),
                 os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')):
        env_path = os.path.join(base, '.env')
        if os.path.isfile(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        os.environ.setdefault(k.strip(), v.strip())
            break

_load_env()

DATABASE_URL = os.environ.get('DATABASE_URL', '')

if not DATABASE_URL:
    raise RuntimeError(
        'DATABASE_URL chua duoc set!\n'
        'Railway: Add PostgreSQL service → DATABASE_URL tu dong inject.\n'
        'Local:   export DATABASE_URL="postgresql://user:pass@host:5432/dbname"'
    )


# ── Connection ────────────────────────────────────────────────────────────────

def _connect():
    return psycopg.connect(DATABASE_URL)


# ── Init DB ───────────────────────────────────────────────────────────────────

def init_db():
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id            SERIAL PRIMARY KEY,
                    username      TEXT    NOT NULL UNIQUE,
                    email         TEXT    NOT NULL UNIQUE,
                    password_hash TEXT    NOT NULL,
                    display_name  TEXT    DEFAULT '',
                    avatar_color  TEXT    DEFAULT '#3CAA64',
                    avatar_path   TEXT    DEFAULT '',
                    wins          INTEGER DEFAULT 0,
                    losses        INTEGER DEFAULT 0,
                    draws         INTEGER DEFAULT 0,
                    role          TEXT    DEFAULT 'user',
                    created_at    TIMESTAMP DEFAULT NOW()
                )
            ''')
            # migration: thêm cột role nếu chưa có
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users'")
            user_cols = [r[0] for r in cur.fetchall()]
            if user_cols and 'role' not in user_cols:
                cur.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
            cur.execute('''
                CREATE TABLE IF NOT EXISTS match_history (
                    id        SERIAL PRIMARY KEY,
                    user_id   INTEGER NOT NULL REFERENCES users(id),
                    opponent  TEXT    NOT NULL,
                    result    TEXT    NOT NULL,
                    color     TEXT    NOT NULL,
                    moves     INTEGER DEFAULT 0,
                    played_at TIMESTAMP DEFAULT NOW()
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS friendships (
                    id         SERIAL PRIMARY KEY,
                    user_id    INTEGER NOT NULL REFERENCES users(id),
                    friend_id  INTEGER NOT NULL REFERENCES users(id),
                    status     TEXT    NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(user_id, friend_id)
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id       SERIAL PRIMARY KEY,
                    from_id  INTEGER NOT NULL REFERENCES users(id),
                    to_id    INTEGER NOT NULL REFERENCES users(id),
                    content  TEXT    NOT NULL,
                    sent_at  TIMESTAMP DEFAULT NOW()
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS matches (
                    id           SERIAL PRIMARY KEY,
                    pin          TEXT    NOT NULL UNIQUE,
                    host         TEXT    NOT NULL,
                    host_display TEXT    DEFAULT '',
                    guest        TEXT    DEFAULT '',
                    guest_display TEXT   DEFAULT '',
                    status       TEXT    NOT NULL DEFAULT 'waiting',
                    created_at   TIMESTAMP DEFAULT NOW()
                )
            ''')
            # migration: thêm cột mới nếu chưa có
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='matches'")
            match_cols = [r[0] for r in cur.fetchall()]
            for col, defn in [('host_display', "TEXT DEFAULT ''"),
                               ('guest_display', "TEXT DEFAULT ''")]:
                if match_cols and col not in match_cols:
                    cur.execute(f'ALTER TABLE matches ADD COLUMN {col} {defn}')
            # migration: đảm bảo cột đúng tên
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='messages'")
            msg_cols = [r[0] for r in cur.fetchall()]
            if msg_cols and 'from_id' not in msg_cols:
                cur.execute('DROP TABLE IF EXISTS messages CASCADE')
                cur.execute('''
                    CREATE TABLE messages (
                        id       SERIAL PRIMARY KEY,
                        from_id  INTEGER NOT NULL REFERENCES users(id),
                        to_id    INTEGER NOT NULL REFERENCES users(id),
                        content  TEXT    NOT NULL,
                        sent_at  TIMESTAMP DEFAULT NOW()
                    )
                ''')
        conn.commit()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def _row(cur, row) -> dict | None:
    if row is None:
        return None
    cols = [d.name for d in cur.description]
    d = dict(zip(cols, row))
    d['display_name'] = d.get('display_name') or d.get('username', '')
    d['avatar_color'] = d.get('avatar_color') or '#3CAA64'
    return d


# ── Users ─────────────────────────────────────────────────────────────────────

def register(username, email, password):
    if len(password) < 4:
        return {'ok': False, 'error': 'Mat khau toi thieu 4 ky tu'}
    if '@' not in email:
        return {'ok': False, 'error': 'Email khong hop le'}
    try:
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    'INSERT INTO users (username,email,password_hash,display_name) '
                    'VALUES(%s,%s,%s,%s)',
                    (username.strip(), email.strip().lower(),
                     _hash(password), username.strip())
                )
            conn.commit()
        return {'ok': True}
    except psycopg.errors.UniqueViolation as e:
        msg = str(e)
        if 'username' in msg:
            return {'ok': False, 'error': 'Ten dang nhap da ton tai'}
        if 'email' in msg:
            return {'ok': False, 'error': 'Email da duoc su dung'}
        return {'ok': False, 'error': 'Loi khong xac dinh'}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


def login(username, password):
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT * FROM users WHERE username=%s AND password_hash=%s',
                (username.strip(), _hash(password))
            )
            row = cur.fetchone()
            if row is None:
                return {'ok': False, 'error': 'Sai ten dang nhap hoac mat khau'}
            return {'ok': True, 'user': _row(cur, row)}


def get_user(username):
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM users WHERE username=%s', (username.strip(),))
            return _row(cur, cur.fetchone())


def get_user_by_id(uid):
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM users WHERE id=%s', (uid,))
            return _row(cur, cur.fetchone())


def update_profile(username, display_name=None, avatar_color=None, avatar_path=None):
    fields, vals = [], []
    if display_name is not None:
        dn = display_name.strip()
        if not dn:
            return {'ok': False, 'error': 'Ten hien thi khong duoc de trong'}
        fields.append('display_name=%s'); vals.append(dn)
    if avatar_color is not None:
        fields.append('avatar_color=%s'); vals.append(avatar_color)
    if avatar_path is not None:
        fields.append('avatar_path=%s'); vals.append(avatar_path)
    if not fields:
        return {'ok': False, 'error': 'Khong co gi de cap nhat'}
    vals.append(username.strip())
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(f'UPDATE users SET {",".join(fields)} WHERE username=%s', vals)
        conn.commit()
    return {'ok': True}


def user_exists(username):
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT 1 FROM users WHERE username=%s', (username.strip(),))
            return cur.fetchone() is not None


# ── Match history ─────────────────────────────────────────────────────────────

def add_match(user_id, opponent, result, color, moves=0):
    col = {'win': 'wins', 'loss': 'losses', 'draw': 'draws'}.get(result)
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'INSERT INTO match_history(user_id,opponent,result,color,moves) '
                'VALUES(%s,%s,%s,%s,%s)',
                (user_id, opponent, result, color, moves)
            )
            if col:
                cur.execute(
                    f'UPDATE users SET {col}={col}+1 WHERE id=%s', (user_id,))
        conn.commit()


def get_match_history(user_id, limit=20):
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT opponent,result,color,moves,played_at FROM match_history '
                'WHERE user_id=%s ORDER BY played_at DESC LIMIT %s',
                (user_id, limit)
            )
            rows = cur.fetchall()
            cols = [d.name for d in cur.description]
            return [dict(zip(cols, r)) for r in rows]


# ── Auto init — chỉ chạy khi DATABASE_URL có sẵn ────────────────────────────
try:
    init_db()
except Exception as e:
    import logging
    logging.getLogger('db').warning(f'init_db skipped: {e}')


# ── Friendships ───────────────────────────────────────────────────────────────

def send_friend_request(from_user_id: int, to_username: str) -> dict:
    """Gửi lời mời kết bạn. status='pending'."""
    to = get_user(to_username)
    if not to:
        return {'ok': False, 'error': 'Khong tim thay nguoi dung'}
    if to['id'] == from_user_id:
        return {'ok': False, 'error': 'Khong the ket ban voi chinh minh'}
    try:
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    'INSERT INTO friendships(user_id, friend_id, status) VALUES(%s,%s,%s) '
                    'ON CONFLICT(user_id, friend_id) DO NOTHING',
                    (from_user_id, to['id'], 'pending')
                )
            conn.commit()
        return {'ok': True}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


def accept_friend_request(user_id: int, from_user_id: int) -> dict:
    """Chấp nhận lời mời — đổi status thành 'accepted' và tạo chiều ngược lại."""
    try:
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE friendships SET status='accepted' "
                    'WHERE user_id=%s AND friend_id=%s',
                    (from_user_id, user_id)
                )
                # tạo chiều ngược lại
                cur.execute(
                    'INSERT INTO friendships(user_id, friend_id, status) VALUES(%s,%s,%s) '
                    'ON CONFLICT(user_id, friend_id) DO UPDATE SET status=%s',
                    (user_id, from_user_id, 'accepted', 'accepted')
                )
            conn.commit()
        return {'ok': True}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


def reject_friend_request(user_id: int, from_user_id: int) -> dict:
    """Từ chối / xóa lời mời."""
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'DELETE FROM friendships WHERE user_id=%s AND friend_id=%s',
                (from_user_id, user_id)
            )
        conn.commit()
    return {'ok': True}


def remove_friend(user_id: int, friend_id: int) -> dict:
    """Xóa bạn bè (cả 2 chiều)."""
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'DELETE FROM friendships WHERE (user_id=%s AND friend_id=%s) '
                'OR (user_id=%s AND friend_id=%s)',
                (user_id, friend_id, friend_id, user_id)
            )
        conn.commit()
    return {'ok': True}


def get_friends(user_id: int) -> list:
    """Danh sách bạn bè đã accepted."""
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT u.id, u.username, u.display_name, u.avatar_path '
                'FROM friendships f JOIN users u ON u.id = f.friend_id '
                'WHERE f.user_id=%s AND f.status=%s',
                (user_id, 'accepted')
            )
            rows = cur.fetchall()
            cols = [d.name for d in cur.description]
            return [dict(zip(cols, r)) for r in rows]


def get_pending_requests(user_id: int) -> list:
    """Danh sách lời mời đang chờ (người khác gửi cho mình)."""
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT u.id, u.username, u.display_name, f.created_at '
                'FROM friendships f JOIN users u ON u.id = f.user_id '
                'WHERE f.friend_id=%s AND f.status=%s',
                (user_id, 'pending')
            )
            rows = cur.fetchall()
            cols = [d.name for d in cur.description]
            return [dict(zip(cols, r)) for r in rows]


def get_friendship_status(user_id: int, other_id: int) -> str:
    """Trả về 'accepted' | 'pending' | 'none'."""
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT status FROM friendships WHERE user_id=%s AND friend_id=%s',
                (user_id, other_id)
            )
            row = cur.fetchone()
    return row[0] if row else 'none'


# ── Messages ──────────────────────────────────────────────────────────────────

def send_message(from_id: int, to_id: int, content: str) -> dict:
    if not content.strip():
        return {'ok': False, 'error': 'Tin nhan trong'}
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'INSERT INTO messages(from_id, to_id, content) VALUES(%s,%s,%s)',
                (from_id, to_id, content.strip())
            )
        conn.commit()
    return {'ok': True}


def get_messages(user_id: int, friend_id: int, limit: int = 50) -> list:
    """Lấy tin nhắn giữa 2 người, mới nhất trước."""
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT id, from_id, to_id, content, sent_at FROM messages '
                'WHERE (from_id=%s AND to_id=%s) OR (from_id=%s AND to_id=%s) '
                'ORDER BY sent_at DESC LIMIT %s',
                (user_id, friend_id, friend_id, user_id, limit)
            )
            rows = cur.fetchall()
            cols = [d.name for d in cur.description]
            return list(reversed([dict(zip(cols, r)) for r in rows]))


# ── Matches (phòng chờ) ───────────────────────────────────────────────────────

def create_match_room(pin: str, host: str, host_display: str = '') -> dict:
    """Tạo phòng mới vào DB."""
    try:
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    'INSERT INTO matches(pin, host, host_display, status) VALUES(%s,%s,%s,%s) '
                    'ON CONFLICT(pin) DO UPDATE SET host=%s, host_display=%s, guest=%s, status=%s, created_at=NOW()',
                    (pin, host, host_display or host, 'waiting',
                     host, host_display or host, '', 'waiting')
                )
            conn.commit()
        return {'ok': True}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


def update_match_room(pin: str, guest: str = None, guest_display: str = None, status: str = None) -> dict:
    """Cập nhật guest hoặc status của phòng."""
    fields, vals = [], []
    if guest         is not None: fields.append('guest=%s');         vals.append(guest)
    if guest_display is not None: fields.append('guest_display=%s'); vals.append(guest_display)
    if status        is not None: fields.append('status=%s');        vals.append(status)
    if not fields:
        return {'ok': False, 'error': 'Nothing to update'}
    vals.append(pin)
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(f'UPDATE matches SET {",".join(fields)} WHERE pin=%s', vals)
        conn.commit()
    return {'ok': True}


def delete_match_room(pin: str) -> dict:
    """Xóa phòng khỏi DB (khi host thoát)."""
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM matches WHERE pin=%s', (pin,))
        conn.commit()
    return {'ok': True}


def get_open_rooms() -> list:
    """Lấy danh sách phòng đang chờ (status='waiting')."""
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT pin, host, host_display, guest, guest_display, created_at FROM matches "
                "WHERE status='waiting' ORDER BY created_at DESC LIMIT 20"
            )
            rows = cur.fetchall()
            cols = [d.name for d in cur.description]
            result = []
            for r in rows:
                d = dict(zip(cols, r))
                if d.get('created_at'):
                    d['created_at'] = str(d['created_at'])
                # dùng host_display nếu có
                d['host'] = d.get('host_display') or d.get('host', '')
                result.append(d)
            return result


# ── Admin ─────────────────────────────────────────────────────────────────────

def get_all_users() -> list:
    """Lấy tất cả user (admin only)."""
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT id, username, email, display_name, wins, losses, draws, role, created_at '
                'FROM users ORDER BY created_at DESC'
            )
            rows = cur.fetchall()
            cols = [d.name for d in cur.description]
            return [dict(zip(cols, r)) for r in rows]


def set_user_role(username: str, role: str) -> dict:
    """Đổi role user (admin only). role: 'user' | 'admin' | 'banned'"""
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE users SET role=%s WHERE username=%s', (role, username))
        conn.commit()
    return {'ok': True}


def delete_user(username: str) -> dict:
    """Xóa user (admin only)."""
    try:
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM users WHERE username=%s', (username,))
            conn.commit()
        return {'ok': True}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


def get_all_messages(limit: int = 100) -> list:
    """Lấy tất cả tin nhắn gần nhất (admin only)."""
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT m.id, u1.username as from_user, u2.username as to_user, '
                'm.content, m.sent_at '
                'FROM messages m '
                'JOIN users u1 ON u1.id = m.from_id '
                'JOIN users u2 ON u2.id = m.to_id '
                'ORDER BY m.sent_at DESC LIMIT %s',
                (limit,)
            )
            rows = cur.fetchall()
            cols = [d.name for d in cur.description]
            return [dict(zip(cols, r)) for r in rows]


def delete_message(msg_id: int) -> dict:
    """Xóa tin nhắn (admin only)."""
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM messages WHERE id=%s', (msg_id,))
        conn.commit()
    return {'ok': True}


def seed_admin() -> dict:
    """Tạo hoặc reset tài khoản admin (username=admin, pass=admin, role=admin)."""
    try:
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    '''INSERT INTO users (username, email, password_hash, display_name, role)
                       VALUES (%s, %s, %s, %s, %s)
                       ON CONFLICT (username) DO UPDATE
                       SET password_hash=%s, role=%s''',
                    ('admin', 'admin@admin.com', _hash('admin'), 'Admin',
                     'admin', _hash('admin'), 'admin')
                )
            conn.commit()
        return {'ok': True, 'msg': 'Admin account ready'}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
