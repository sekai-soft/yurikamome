import json
import secrets
from flask import request, Blueprint, render_template, redirect, make_response
from twikit import Client
from .helpers import create_session, catches_exceptions, query_session

pages_blueprint = Blueprint("pages", __name__)


@pages_blueprint.route('/')
@catches_exceptions
def index():
    twid = None
    session_id = request.cookies.get('session_id')
    if session_id:
        session_row = query_session(session_id)
        cookies = json.loads(session_row['cookies'])
        twid = cookies.get('twid')
    return render_template('index.html', twid=twid)


@pages_blueprint.route('/twitter_auth', methods=['POST'])
async def twitter_auth():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    mfa = request.form.get('mfa', None)

    client = Client('en-US')
    await client.login(
        auth_info_1=username,
        auth_info_2=email,
        password=password,
        totp_secret=mfa
    )
    cookies = client.get_cookies()
    
    session_id = secrets.token_hex(10)
    create_session(session_id, json.dumps(cookies))

    resp = make_response(redirect('/'))
    resp.set_cookie('session_id', session_id)
    return resp
