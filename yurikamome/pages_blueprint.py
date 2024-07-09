import secrets
from flask import request, Blueprint, render_template, redirect, make_response
from twikit import Client
from .helpers import create_session, catches_exceptions

pages_blueprint = Blueprint("pages", __name__)


@pages_blueprint.route('/')
@catches_exceptions
def index():
    return render_template('index.html')


@pages_blueprint.route('/twitter_auth', methods=['POST'])
def twitter_auth():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    client = Client('en-US')
    client.login(
        auth_info_1=username,
        auth_info_2=email,
        password=password
    )
    cookies = client.get_cookies()
    
    session_id = secrets.token_hex(10)
    create_session(session_id, str(cookies))

    resp = make_response(redirect('/'))
    resp.set_cookie('session_id', session_id)
    return resp
