import os
import sys
import sqlite3
from flask import g


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
