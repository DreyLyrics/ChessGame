"""
DataBase/db.py — ChessGamePlay database
Tables: users, match_history
"""

import sqlite3
import hashlib
import os

_HERE   = os.path.dirname(os.path.abspath(__file__))

# Khi chay tu PyInstaller exe, dung bien moi truong CHESS_DB_DIR
# de luu chess.db vao thu muc co the ghi duoc (ben canh exe)
if os.environ.get('CHESS_DB_DIR'):
    _DB_DIR = os.environ['CHESS_DB_DIR']
else:
    _DB_DIR = _HERE

DB_PATH = os.path.join(_DB_DIR, 'chess.db')


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _add_col(conn, table, col, defn):
    cols = [r[1] for r in conn.execute(f'PRAGMA table_info({table})')]
    if col not in cols:
        conn.execute(f'ALTER TABLE {table} ADD COLUMN {col} {defn}')


def init_db():
    with _connect() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT    NOT NULL UNIQUE,
            email         TEXT    NOT NULL UNIQUE,
            password_hash TEXT    NOT NULL,
            display_name  TEXT    DEFAULT '',
            avatar_color  TEXT    DEFAULT '#3CAA64',
            wins          INTEGER DEFAULT 0,
            losses        INTEGER DEFAULT 0,
            draws         INTEGER DEFAULT 0,
            created_at    TEXT    DEFAULT (datetime('now','localtime'))
        )''')
        for col, defn in [
            ('display_name', "TEXT DEFAULT ''"),
            ('avatar_color', "TEXT DEFAULT '#3CAA64'"),
            ('avatar_path',  "TEXT DEFAULT ''"),
            ('wins',   'INTEGER DEFAULT 0'),
            ('losses', 'INTEGER DEFAULT 0'),
            ('draws',  'INTEGER DEFAULT 0'),
        ]:
            _add_col(conn, 'users', col, defn)

        conn.execute('''CREATE TABLE IF NOT EXISTS match_history (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id   INTEGER NOT NULL REFERENCES users(id),
            opponent  TEXT    NOT NULL,
            result    TEXT    NOT NULL,
            color     TEXT    NOT NULL,
            moves     INTEGER DEFAULT 0,
            played_at TEXT    DEFAULT (datetime('now','localtime'))
        )''')
        conn.commit()


def _hash(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


def _to_dict(row):
    if row is None:
        return None
    d = dict(row)
    d['display_name'] = d.get('display_name') or d.get('username', '')
    d['avatar_color'] = d.get('avatar_color') or '#3CAA64'
    return d


# ── users ─────────────────────────────────────────────────────────────────────

def register(username, email, password):
    if len(password) < 4:
        return {'ok': False, 'error': 'Mat khau toi thieu 4 ky tu'}
    if '@' not in email:
        return {'ok': False, 'error': 'Email khong hop le'}
    try:
        with _connect() as conn:
            conn.execute(
                'INSERT INTO users (username,email,password_hash,display_name) VALUES(?,?,?,?)',
                (username.strip(), email.strip().lower(), _hash(password), username.strip())
            )
            conn.commit()
        return {'ok': True}
    except sqlite3.IntegrityError as e:
        msg = str(e)
        if 'username' in msg:
            return {'ok': False, 'error': 'Ten dang nhap da ton tai'}
        if 'email' in msg:
            return {'ok': False, 'error': 'Email da duoc su dung'}
        return {'ok': False, 'error': 'Loi khong xac dinh'}


def login(username, password):
    with _connect() as conn:
        row = conn.execute(
            'SELECT * FROM users WHERE username=? AND password_hash=?',
            (username.strip(), _hash(password))
        ).fetchone()
    if row is None:
        return {'ok': False, 'error': 'Sai ten dang nhap hoac mat khau'}
    return {'ok': True, 'user': _to_dict(row)}


def get_user(username):
    with _connect() as conn:
        row = conn.execute('SELECT * FROM users WHERE username=?',
                           (username.strip(),)).fetchone()
    return _to_dict(row)


def get_user_by_id(uid):
    with _connect() as conn:
        row = conn.execute('SELECT * FROM users WHERE id=?', (uid,)).fetchone()
    return _to_dict(row)


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
    with _connect() as conn:
        conn.execute(f'UPDATE users SET {",".join(fields)} WHERE username=?', vals)
        conn.commit()
    return {'ok': True}


def user_exists(username):
    with _connect() as conn:
        return conn.execute('SELECT 1 FROM users WHERE username=?',
                            (username.strip(),)).fetchone() is not None


# ── match history ─────────────────────────────────────────────────────────────

def add_match(user_id, opponent, result, color, moves=0):
    """result: 'win' | 'loss' | 'draw'"""
    with _connect() as conn:
        conn.execute(
            'INSERT INTO match_history(user_id,opponent,result,color,moves) VALUES(?,?,?,?,?)',
            (user_id, opponent, result, color, moves)
        )
        col = {'win': 'wins', 'loss': 'losses', 'draw': 'draws'}.get(result)
        if col:
            conn.execute(f'UPDATE users SET {col}={col}+1 WHERE id=?', (user_id,))
        conn.commit()


def get_match_history(user_id, limit=20):
    with _connect() as conn:
        rows = conn.execute(
            'SELECT opponent,result,color,moves,played_at FROM match_history '
            'WHERE user_id=? ORDER BY played_at DESC LIMIT ?',
            (user_id, limit)
        ).fetchall()
    return [dict(r) for r in rows]


init_db()
