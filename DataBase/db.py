"""
DataBase/db.py — ChessGamePlay database
Chỉ dùng PostgreSQL (psycopg3).
DATABASE_URL được inject tự động bởi Railway.
"""

import os
import hashlib
import psycopg

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
                    created_at    TIMESTAMP DEFAULT NOW()
                )
            ''')
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


# ── Auto init ─────────────────────────────────────────────────────────────────
init_db()
