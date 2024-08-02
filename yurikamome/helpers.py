import os
import sys
import secrets
import sqlite3
import json
from functools import wraps
from flask import g, render_template, request, jsonify
from twikit import Client


def env_or_bust(env: str):
    if env not in os.environ:
        print(f"Environment variable {env} is required")
        sys.exit(1)
    return os.environ[env]

SQLITE_DB = env_or_bust('SQLITE_DB')


def get_host_url_or_bust():
    host = env_or_bust('HOST')
    scheme = env_or_bust('SCHEME')
    return f"{scheme}://{host}"


def random_secret():
    return secrets.token_hex(10)


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(SQLITE_DB, check_same_thread=False)
    return db


def query_db(query, args=(), one=False):
    db = get_db()
    db.row_factory = sqlite3.Row
    cur = db.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

CREATE_APP_SQL = """
INSERT INTO apps (id, name, website, redirect_uris, client_id, client_secret, vapid_key, scopes)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
"""


def create_app(app_info):
    db = get_db()
    db.execute(CREATE_APP_SQL, app_info)
    db.commit()


def query_app_by_client_id(client_id: str):
    return query_db('SELECT * FROM apps WHERE client_id = ?', (client_id,), one=True)


def update_app_session_id(client_id: str, session_id: str):
    db = get_db()
    db.execute("UPDATE apps SET session_id = ? WHERE client_id = ?", (session_id, client_id))
    db.execute("UPDATE apps SET last_used_at = datetime('now') WHERE client_id = ?", (client_id,))
    db.commit()


def update_app_authorization_code(client_id: str, authorization_code: str):
    db = get_db()
    db.execute("UPDATE apps SET authorization_code = ? WHERE client_id = ?", (authorization_code, client_id))
    db.execute("UPDATE apps SET last_used_at = datetime('now') WHERE client_id = ?", (client_id,))
    db.commit()


def update_app_access_token(client_id: str, access_token: str):
    db = get_db()
    db.execute("UPDATE apps SET access_token = ? WHERE client_id = ?", (access_token, client_id))
    db.execute("UPDATE apps SET last_used_at = datetime('now') WHERE client_id = ?", (client_id,))
    db.commit()


def create_session(session_id: str, cookies: str, username: str):
    db = get_db()
    db.execute("INSERT INTO sessions (session_id, cookies, username) VALUES (?, ?, ?)", (session_id, cookies, username))
    db.commit()


def query_session(session_id: str):
    return query_db('SELECT * FROM sessions WHERE session_id = ?', (session_id,), one=True)


def delete_session(session_id: str):
    db = get_db()
    db.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
    db.commit()


def query_cookies_by_access_token(access_token: str):
    app_row = query_db('SELECT session_id FROM apps WHERE access_token = ?', (access_token,), one=True)
    if not app_row:
        return None
    session_id = app_row['session_id']
    session_row = query_db('SELECT * FROM sessions WHERE session_id = ?', (session_id,), one=True)
    if not session_row:
        return None
    db = get_db()
    db.execute('UPDATE apps SET last_used_at = datetime("now") WHERE session_id = ?', (session_id,))
    db.commit()
    return session_row['cookies']


# TODO: does not work
def catches_exceptions(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            if os.getenv('DEBUG', '0') == '1':
                raise e
            # TODO: sentry
            # capture_exception(e)
            return render_template('error.html', error=str(e))
    return decorated_function


def session_authenticated(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        g.session_row = None
        session_id = request.cookies.get('session_id')
        if session_id:
            session_row = query_session(session_id)
            if session_row:
                g.session_row = session_row
        return f(*args, **kwargs)
    return decorated_function


def async_token_authenticated(f):
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        g.client = None
        auth_header = request.headers.get('Authorization')
        had_auth = False
        if auth_header and auth_header.startswith('Bearer '):
            access_token = auth_header[len('Bearer '):]
            cookies = query_cookies_by_access_token(access_token)
            if cookies:
                g.client = Client()
                g.client.set_cookies(json.loads(cookies))
                had_auth = True
        if not had_auth:
            return jsonify({
                'error': 'The access token is invalid'
            }), 401
        return await f(*args, **kwargs)
    return decorated_function


def json_or_form(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        g.json_or_form = None
        if request.is_json:
            g.json_or_form = request.json
        else:
            g.json_or_form = request.form
        return f(*args, **kwargs)
    return decorated_function
