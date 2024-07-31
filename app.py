import os
import sentry_sdk
import werkzeug.exceptions
from sentry_sdk import capture_exception
from flask import Flask, g
from dotenv import load_dotenv
from yurikamome.mastodon_meta_blueprint import meta_blueprint
from yurikamome.mastodon_timelines_blueprint import timelines_blueprint
from yurikamome.pages_blueprint import pages_blueprint
from yurikamome.helpers import get_db

load_dotenv()

if os.getenv('SENTRY_DSN'):
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN')
    )

app = Flask(__name__, template_folder='templates', static_folder='static')
app.register_blueprint(pages_blueprint, url_prefix='/')
app.register_blueprint(meta_blueprint, url_prefix='/')
app.register_blueprint(timelines_blueprint, url_prefix='/')


@app.errorhandler(werkzeug.exceptions.BadRequest)
def handle_bad_request(e):
    capture_exception(e)
    return 'bad request!', 400


@app.teardown_appcontext
def close_connection(_):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


@app.cli.group()
def sqlite():
    """sqlite commands."""
    pass


@sqlite.command()
def init():
    """Update sqlite database."""
    init_db()
