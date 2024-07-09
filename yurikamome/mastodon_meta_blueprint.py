import secrets
import time
import uuid
from urllib.parse import unquote, quote
from flask import jsonify, request, render_template, Blueprint, g, redirect
from .helpers import env_or_bust, get_host_url_or_bust, update_app_session_id, \
    catches_exceptions, create_app, query_app_by_client_id, authenticated

HOST = env_or_bust('HOST')
HOST_URL = get_host_url_or_bust()
SQLITE_DB = env_or_bust('SQLITE_DB')

meta_blueprint = Blueprint('mastodon_meta', __name__)


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
        'registrations': False,
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
def create_app_route():
    if 'client_name' not in request.json:
        return jsonify({
            'error': 'client_name is required'
        }), 422
    client_name = unquote(request.json['client_name'])

    if 'redirect_uris' not in request.json:
        return jsonify({
            'error': 'redirect_uris is required'
        }), 422
    redirect_uris = unquote(request.json['redirect_uris'])

    scopes = request.json.get('scopes', 'read')
    website = request.json.get('website', None)

    app_id = str(uuid.uuid4())
    client_id = str(uuid.uuid4())
    client_secret = secrets.token_hex(10)
    vapid_key = secrets.token_hex(10)

    create_app((
        app_id,
        client_name,
        website,
        redirect_uris,
        client_id,
        client_secret,
        vapid_key,
        scopes,
    ))

    return jsonify({
        'id': app_id,
        'name': client_name,
        'website': website,
        "redirect_uri": redirect_uris,
        'client_id': client_id,
        'client_secret': client_secret,
        'vapid_key' : vapid_key,
    })


@meta_blueprint.route('/oauth/authorize')
@authenticated
@catches_exceptions
def oauth_authorize():
    if not g.session_row:
        return redirect(f'/login?from={quote(request.full_path)}')

    if 'response_type' not in request.args or request.args['response_type'] != 'code':
        return render_template('oauth_authorize.html', erorr="response_type must be 'code'")

    if 'client_id' not in request.args:
        return render_template('oauth_authorize.html', erorr="client_id is required")
    client_id = request.args['client_id']

    app_row = query_app_by_client_id(client_id)
    if not app_row:
        return render_template('oauth_authorize.html', erorr="client_id is not found")

    if 'redirect_uri' not in request.args:
        return render_template('oauth_authorize.html', erorr="redirect_uri is required")
    redirect_uri = request.args['redirect_uri']
    app_redirect_uris = app_row['redirect_uris']
    if redirect_uri not in app_redirect_uris:
        return render_template('oauth_authorize.html', erorr="redirect_uri is not included in the declared list when app is created")

    scope_set = set(request.args.get('scope', 'read').split(' '))
    app_scope_set = set(app_row['scopes'].split(' '))
    if not scope_set.issubset(app_scope_set):
        return render_template('oauth_authorize.html', erorr="scope is not a subset of the declared set when app is created")

    # TODO
    force_login = bool(request.args.get('force_login', 'false'))
    lang = request.args.get('lang', 'en')

    update_app_session_id(client_id, g.session_row['session_id'])

    # TODO: handle urn:ietf:wg:oauth:2.0:oob

    return render_template(
        'oauth_authorize.html',
        username=g.session_row['username'],
        app_name=app_row['name'],
        app_website=app_row['website'],
        app_scopes=app_row['scopes']
    )


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
