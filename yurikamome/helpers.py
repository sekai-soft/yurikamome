import os
import sys
import sqlite3
from functools import wraps
from flask import g, render_template


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


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(SQLITE_DB)
    return db


def query_db(query, args=(), one=False):
    db = get_db()
    db.row_factory = sqlite3.Row
    cur = db.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def update_last_used_at(client_id: str):
    db = get_db()
    db.execute("UPDATE apps SET last_used_at = datetime('now') WHERE client_id = ?", (client_id,))
    db.commit()


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
