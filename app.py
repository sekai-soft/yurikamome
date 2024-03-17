import os
import sys
import secrets
import time
from flask import Flask, jsonify, request
from twikit import Client
from twikit.utils import Endpoint
from mastodon_twitter_shim.utils import _tweet_to_status


def env_or_bust(env: str):
    if env not in os.environ:
        print(f"Environment variable {env} is required")
        sys.exit(1)
    return os.environ[env]

HOST = env_or_bust('HOST')
SCHEME = env_or_bust('SCHEME')
HOST_URL = f"{SCHEME}://{HOST}"
TWITTER_USERNAME = env_or_bust('TWITTER_USERNAME')
TWITTER_EMAIL = env_or_bust('TWITTER_EMAIL')
TWITTER_PASSWORD = env_or_bust('TWITTER_PASSWORD')
SAVED_CREDENTIALS_PATH = env_or_bust('SAVED_CREDENTIALS_PATH')
PREDEFINED_TOKEN = env_or_bust('PREDEFINED_TOKEN')


client = Client('en-US')
if os.path.exists(SAVED_CREDENTIALS_PATH):
    print(f"Loading cookies from {SAVED_CREDENTIALS_PATH}")
    client.load_cookies(SAVED_CREDENTIALS_PATH)
else:
    client.login(
        auth_info_1=TWITTER_USERNAME,
        auth_info_2=TWITTER_EMAIL,
        password=TWITTER_PASSWORD
    )
    client.save_cookies(SAVED_CREDENTIALS_PATH)
    print(f"Saved cookies to {SAVED_CREDENTIALS_PATH}")


app = Flask(__name__)



@app.route('/api/v1/timelines/home')
def _home_timeline():
    # TODO: ACTUALLY CHECK TOKEN
    # TODO: can cache response for a while
    tweets = client.get_timeline(timeline_endpoint=Endpoint.HOME_LATEST_TIMELINE)
    statues = []
    for t in tweets:
        statues.append(_tweet_to_status(t, HOST_URL))
    return jsonify(statues)


@app.route('/api/v1/instance')
def _instance():
    return jsonify({
        'uri': HOST_URL,
        'title': 'Mastodon Twitter shim',
        'short_description': 'Use Twitter with Mastodon clients',
        'description': 'Use Twitter with Mastodon clients',
        'email': f'admin@{HOST}',
        # TODO: should stick or update with Mastodon version?
        'version': '4.2.7',
        'stats': {
            # TODO: change if multitenant
            'user_count': 1,
            'status_count': 0,
            'domain_count': 0,
        },
        'thumbnail': None,
        'languages': [],
        'registrations': True,
        'approval_required': False,
        'invites_enabled': False,
        'configuration': {
            "statuses": {
                "max_characters": 280,
                "max_media_attachments": 4,
            },
        },
        'contact_account': None,
        'rules': []
    })


@app.route('/api/v1/apps', methods=['POST'])
def _create_app():
    client_name = request.json['client_name']
    redirect_uris = request.json['redirect_uris']
    website = request.json.get('website', None)
    # TODO: better to persist apps?
    return jsonify({
        'id': client_name,
        'name': client_name,
        'website': website,
        "redirect_uri": redirect_uris,
        'client_id': client_name,
        'client_secret': secrets.token_hex(10)
    })


@app.route('/oauth/authorize')
def _oauth_authorize():
    # TODO: ACTUALLY AUTHORIZE FIRST
    return f"""
<a href='{request.args['redirect_uri']}?code=0'>Just authorize</a>
"""


@app.route('/oauth/token', methods=['POST'])
def _oauth_get_token():
    return jsonify({
        'access_token': PREDEFINED_TOKEN,
        "token_type": "Bearer",
        # TODO: could limit scope
        "scope": "read write follow push",
        "created_at": int(time.time())
    })


@app.route('/api/v1/accounts/verify_credentials')
def _verify_credentials():
    # TODO
    return jsonify({ 
        'id': '0',
        'username': '',
        'acct': '',
        'url': '',
        'display_name': '',
        'note': '',
        'avatar': '',
        'avatar_static': '',
        'header': '',
        'header_static': '',
        'locked': False,
        'fields': [],
        'emojis': [],
        'bot': False,
        'group': False,
        'discoverable': False,
        'created_at': '2023-02-01T00:00:00.000Z',
        'last_status_at': '2023-02-01T00:00:00.000Z',
        'statuses_count': 0,
        'followers_count': 0,
        'following_count': 0
    })
