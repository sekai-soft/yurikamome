import secrets
import time
from urllib.parse import unquote
from flask import jsonify, request, render_template, Blueprint
from .helpers import env_or_bust, get_host_url_or_bust

HOST = env_or_bust('HOST')
HOST_URL = get_host_url_or_bust()
SQLITE_DB = env_or_bust('SQLITE_DB')

meta_blueprint = Blueprint('meta', __name__)


@meta_blueprint.route('/api/v1/instance')
def instance():
    return jsonify({
        'uri': HOST_URL,
        'title': 'Yurikamome',
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


@meta_blueprint.route('/api/v1/apps', methods=['POST'])
def create_app():
    if 'client_name' not in request.json:
        return jsonify({
            'error': 'client_name is required'
        }), 422
    client_name = unquote(request.json['client_name'])

    if 'redirect_uris' not in request.json:
        return jsonify({
            'error': 'redirect_uris is required'
        }), 422
    redirect_uris = request.json['redirect_uris']

    scopes = request.json.get('scopes', 'read').split(' ')
    website = request.json.get('website', None)

    return jsonify({
        'id': client_name,
        'name': client_name,
        'website': website,
        "redirect_uri": redirect_uris,
        'client_id': client_name,
        'client_secret': secrets.token_hex(10)
    })


@meta_blueprint.route('/oauth/authorize')
def oauth_authorize():
    return render_template('oauth_authorize.html')


@meta_blueprint.route('/oauth/token', methods=['POST'])
def oauth_get_token():
    return jsonify({
        'access_token': 'TODO',
        "token_type": "Bearer",
        # TODO: could limit scope
        "scope": "read write follow push",
        "created_at": int(time.time())
    })


@meta_blueprint.route('/api/v1/accounts/verify_credentials')
def verify_credentials():
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
