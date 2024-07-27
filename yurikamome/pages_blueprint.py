import json
import secrets
from urllib.parse import unquote, quote
from flask import request, Blueprint, render_template, redirect, make_response, g
from twikit import Client
from .helpers import create_session, catches_exceptions, session_authenticated, delete_session, random_secret

pages_blueprint = Blueprint("pages", __name__)


@pages_blueprint.route('/')
@session_authenticated
@catches_exceptions
def index():
    username = None
    if g.session_row:
        username = g.session_row['username']
    return render_template('index.html', username=username)


@pages_blueprint.route('/login')
@session_authenticated
@catches_exceptions
def login():
    if g.session_row:
        return redirect('/')
    from_path = quote(request.args.get('from', '/'))
    return render_template('login.html', from_path=from_path)


@pages_blueprint.route('/logout')
@session_authenticated
@catches_exceptions
def logout():
    if g.session_row:
        delete_session(g.session_row['session_id'])
    resp = make_response(redirect('/'))
    resp.delete_cookie('session_id')
    return resp


@pages_blueprint.route('/twitter_auth', methods=['POST'])
async def twitter_auth():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    mfa = request.form.get('mfa', None)
    from_path = unquote(request.args.get('from', '/'))

    client = Client('en-US')
    await client.login(
        auth_info_1=username,
        auth_info_2=email,
        password=password,
        totp_secret=mfa
    )
    cookies = client.get_cookies()
    
    session_id = random_secret()
    create_session(session_id, json.dumps(cookies), username)

    resp = make_response(redirect(from_path))
    resp.set_cookie('session_id', session_id)
    return resp
