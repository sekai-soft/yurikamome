from flask import Flask
from yurikamome.meta import meta_blueprint
from yurikamome.timelines import timelines_blueprint

app = Flask(__name__, template_folder='templates')
app.register_blueprint(meta_blueprint, url_prefix='/')
app.register_blueprint(timelines_blueprint, url_prefix='/')
