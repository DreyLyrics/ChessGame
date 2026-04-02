"""
DataBase/db.py — ChessGamePlay database
- PostgreSQL (psycopg3) khi có DATABASE_URL env var  → dùng trên Railway
- SQLite fallback khi chạy local

Railway setup:
    1. Vào Railway project → Add Service → PostgreSQL
    2. DATABASE_URL tự động được inject vào env
"""

import os
import hashlib

# ── Detect mode ───────────────────────────────────────────────────────────────
DATABASE_URL = os.environ.get('DATABASE_URL', '')
USE_POSTGRES = bool(DATABASE_URL)

# ── SQLite path (local fallback) ──────────────────────────────────────────────
_HERE   = os.path.dirname(os.path.abspath(__file__))
_DB_DIR = os.environ.get('CHESS_DB_DIR', _HERE)
DB_PATH = os.path.join(_DB_DIR, 'chess.db')


# ── Connection helpers ────────────────────────────────────────────────────────

def _connect_pg():
    import psycopg
    return psycopg.connect(DATABASE_URL)


def _connect_sqlite():
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _connect():
    return _connect_pg() if USE_POSTGRES else _connect_sqlite()


# ── SQL dialect helpers ───────────────────────────────────────────────────────
# PostgreSQL dùng %s, SQLite dùng ?

def _ph():
    """Placeholder cho query param."""
    return '%s' if USE_POSTGRES else '?'

def _q(sql: str) -> str:
    """Chuyển ? → %s nếu dùng Postgres."""
    if USE_POSTGRES:
        return sql.replace('?', '%s')
    return sql

def _serial():
    return 'SERIAL' if USE_POSTGRES else 'INTEGER'

def _autoincrement():
    return '' if USE_POSTGRES else 'AUTOINCREMENT'

def _now():
    return 'NOW()' if USE_POSTGRES else "datetime('now','localtime')"


# ── Init DB ───────────────────────────────────────────────────────────────────

def init_db():
    serial = _serial()
    ai     = _autoincrement()
    now    = _now()

    with _connect() as conn:
        cur = conn.cursor()

        if USE_POSTGRES:
            cur.execute(f'''
                CREATE TABLE IF NOT EXISTS users (
                    id            {serial} PRIMARY KEY,
                    username      TEXT    NOT NULL UNIQUE,
                    email         TEXT    NOT NULL UNIQUE,
                    password_hash TEXT    NOT NULL,
                    display_name  TEXT    DEFAULT '',
                    avatar_color  TEXT    DEFAULT '#3CAA64',
                    avatar_path   TEXT    DEFAULT '',
                    wins          INTEGER DEFAULT 0,
                    losses        INTEGER DEFAULT 0,
                    draws         INTEGER DEFAULT 0,
                    created_at    TIMESTAMP DEFAULT NOW()
                )
            ''')
            cur.execute(f'''
                CREATE TABLE IF NOT EXISTS match_history (
                    id        {serial} PRIMARY KEY,
                    user_id   INTEGER NOT NULL REFERENCES users(id),
                    opponent  TEXT    NOT NULL,
                    result    TEXT    NOT NULL,
                    color     TEXT    NOT NULL,
                    moves     INTEGER DEFAULT 0,
                    played_at TIMESTAMP DEFAULT NOW()
                )
            ''')
        else:
            cur.execute(f'''CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY {ai},
                username      TEXT    NOT NULL UNIQUE,
                email         TEXT    NOT NULL UNIQUE,
                password_hash TEXT    NOT NULL,
                display_name  TEXT    DEFAULT '',
                avatar_color  TEXT    DEFAULT '#3CAA64',
                avatar_path   TEXT    DEFAULT '',
                wins          INTEGER DEFAULT 0,
                losses        INTEGER DEFAULT 0,
                draws         INTEGER DEFAULT 0,
                created_at    TEXT    DEFAULT ({now})
            )''')
            cur.execute(f'''CREATE TABLE IF NOT EXISTS match_history (
                id        INTEGER PRIMARY KEY {ai},
                user_id   INTEGER NOT NULL REFERENCES users(id),
                opponent  TEXT    NOT NULL,
                result    TEXT    NOT NULL,
                color     TEXT    NOT NULL,
                moves     INTEGER DEFAULT 0,
                played_at TEXT    DEFAULT ({now})
            )''')

            # migration: thêm cột mới nếu chưa có (SQLite only)
            for col, defn in [
                ('display_name', "TEXT DEFAULT ''"),
                ('avatar_color', "TEXT DEFAULT '#3CAA64'"),
                ('avatar_path',  "TEXT DEFAULT ''"),
                ('wins',   'INTEGER DEFAULT 0'),
                ('losses', 'INTEGER DEFAULT 0'),
                ('draws',  'INTEGER DEFAULT 0'),
            ]:
                cols = [r[1] for r in cur.execute('PRAGMA table_info(users)')]
                if col not in cols:
                    cur.execute(f'ALTER TABLE users ADD COLUMN {col} {defn}')

        conn.commit()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def _row_to_dict(row, cursor=None) -> dict | None:
    if row is None:
        return None
    if USE_POSTGRES and cursor:
        cols = [d.name for d in cursor.description]
        d = dict(zip(cols, row))
    else:
        d = dict(row)
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
            cur = conn.cursor()
            cur.execute(_q(
                'INSERT INTO users (username,email,password_hash,display_name) VALUES(?,?,?,?)'),
                (username.strip(), email.strip().lower(), _hash(password), username.strip())
            )
            conn.commit()
        return {'ok': True}
    except Exception as e:
        msg = str(e).lower()
        if 'username' in msg or 'unique' in msg and 'username' in str(e):
            return {'ok': False, 'error': 'Ten dang nhap da ton tai'}
        if 'email' in msg:
            return {'ok': False, 'error': 'Email da duoc su dung'}
        return {'ok': False, 'error': 'Loi khong xac dinh'}


def login(username, password):
    with _connect() as conn:
        cur = conn.cursor()
        cur.execute(_q(
            'SELECT * FROM users WHERE username=? AND password_hash=?'),
            (username.strip(), _hash(password))
        )
        row = cur.fetchone()
    if row is None:
        return {'ok': False, 'error': 'Sai ten dang nhap hoac mat khau'}
    return {'ok': True, 'user': _row_to_dict(row, cur)}


def get_user(username):
    with _connect() as conn:
        cur = conn.cursor()
        cur.execute(_q('SELECT * FROM users WHERE username=?'), (username.strip(),))
        row = cur.fetchone()
    return _row_to_dict(row, cur)


def get_user_by_id(uid):
    with _connect() as conn:
        cur = conn.cursor()
        cur.execute(_q('SELECT * FROM users WHERE id=?'), (uid,))
        row = cur.fetchone()
    return _row_to_dict(row, cur)


def update_profile(username, display_name=None, avatar_color=None, avatar_path=None):
    fields, vals = [], []
    if display_name is not None:
        dn = display_name.strip()
        if not dn:
            return {'ok': False, 'error': 'Ten hien thi khong duoc de trong'}
        fields.append('display_name=?'); vals.append(dn)
    if avatar_color is not None:
        fields.append('avatar_color=?'); vals.append(avatar_color)
    if avatar_path is not None:
        fields.append('avatar_path=?'); vals.append(avatar_path)
    if not fields:
        return {'ok': False, 'error': 'Khong co gi de cap nhat'}
    vals.append(username.strip())
    sql = _q(f'UPDATE users SET {",".join(fields)} WHERE username=?')
    with _connect() as conn:
        cur = conn.cursor()
        cur.execute(sql, vals)
        conn.commit()
    return {'ok': True}


def user_exists(username):
    with _connect() as conn:
        cur = conn.cursor()
        cur.execute(_q('SELECT 1 FROM users WHERE username=?'), (username.strip(),))
        return cur.fetchone() is not None


# ── Match history ─────────────────────────────────────────────────────────────

def add_match(user_id, opponent, result, color, moves=0):
    col = {'win': 'wins', 'loss': 'losses', 'draw': 'draws'}.get(result)
    with _connect() as conn:
        cur = conn.cursor()
        cur.execute(_q(
            'INSERT INTO match_history(user_id,opponent,result,color,moves) VALUES(?,?,?,?,?)'),
            (user_id, opponent, result, color, moves)
        )
        if col:
            cur.execute(_q(f'UPDATE users SET {col}={col}+1 WHERE id=?'), (user_id,))
        conn.commit()


def get_match_history(user_id, limit=20):
    with _connect() as conn:
        cur = conn.cursor()
        cur.execute(_q(
            'SELECT opponent,result,color,moves,played_at FROM match_history '
            'WHERE user_id=? ORDER BY played_at DESC LIMIT ?'),
            (user_id, limit)
        )
        rows = cur.fetchall()
        if USE_POSTGRES:
            cols = [d.name for d in cur.description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(r) for r in rows]


# ── Auto init ─────────────────────────────────────────────────────────────────
init_db()
