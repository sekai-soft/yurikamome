from flask import Flask, g
from yurikamome.meta import meta_blueprint
from yurikamome.timelines import timelines_blueprint
from yurikamome.helpers import get_db


app = Flask(__name__, template_folder='templates', static_folder='static')
app.register_blueprint(meta_blueprint, url_prefix='/')
app.register_blueprint(timelines_blueprint, url_prefix='/')


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
