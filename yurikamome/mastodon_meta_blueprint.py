import time
import uuid
from urllib.parse import unquote, quote
from twikit import User
from flask import jsonify, request, render_template, Blueprint, g, redirect, make_response
from .helpers import env_or_bust, get_host_url_or_bust, update_app_session_id, \
    create_app, query_app_by_client_id, session_authenticated, update_app_authorization_code, random_secret, \
    update_app_access_token, async_token_authenticated, json_or_form

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
@json_or_form
def create_app_route():
    if 'client_name' not in g.json_or_form:
        return jsonify({
            'error': 'client_name is required'
        }), 422
    client_name = unquote(g.json_or_form['client_name'])

    if 'redirect_uris' not in g.json_or_form:
        return jsonify({
            'error': 'redirect_uris is required'
        }), 422
    redirect_uris = unquote(g.json_or_form['redirect_uris'])

    scopes = g.json_or_form.get('scopes', 'read')
    website = g.json_or_form.get('website', None)

    app_id = str(uuid.uuid4())
    client_id = str(uuid.uuid4())
    client_secret = random_secret()
    vapid_key = random_secret()

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
@session_authenticated
# @catches_exceptions
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

    force_login = bool(request.args.get('force_login'))
    if force_login:
        resp = make_response(
            redirect(f'/login?from={quote(request.full_path)}'))
        resp.delete_cookie('session_id')
        return resp

    # TODO: handle urn:ietf:wg:oauth:2.0:oob
    update_app_session_id(client_id, g.session_row['session_id'])

    lang = request.args.get('lang', 'en') # TODO: render different language
    return render_template(
        'oauth_authorize.html',
        username=g.session_row['username'],
        app_name=app_row['name'],
        app_website=app_row['website'],
        app_scopes=app_row['scopes'],
        client_id=client_id,
        redirect_uri=redirect_uri,
    )


@meta_blueprint.route('/oauth/authorize', methods=['POST'])
def oauth_authorize_post():
    if 'client_id' not in request.form:
        # TODO: catch exceptions and show toast
        raise RuntimeError("client_id is required") 
    client_id = request.form['client_id']

    app_row = query_app_by_client_id(client_id)
    if not app_row:
        raise RuntimeError("client_id is not found")

    if 'redirect_uri' not in request.form:
        raise RuntimeError("redirect_uri is required")
    redirect_uri = request.form['redirect_uri']
    if redirect_uri not in app_row['redirect_uris']:
        raise RuntimeError("redirect_uri is not included in the declared list when app is created")
    
    scope_set = set(request.form.get('scope', 'read').split(' '))
    app_scope_set = set(app_row['scopes'].split(' '))
    if not scope_set.issubset(app_scope_set):
        return render_template('oauth_authorize.html', erorr="scope is not a subset of the declared set when app is created")
    
    authorization_code = random_secret()
    update_app_authorization_code(client_id, authorization_code)

    return redirect(f'{redirect_uri}?code={authorization_code}')


@meta_blueprint.route('/oauth/token', methods=['POST'])
@json_or_form
def oauth_get_token():
    if 'grant_type' not in g.json_or_form:
        return jsonify({
            'error': 'grant_type is required'
        }), 422
    grant_type = g.json_or_form['grant_type']
    if grant_type not in ('authorization_code', 'client_credentials'):
        return jsonify({
            'error': 'grant_type must be authorization_code or client_credentials'
        }), 422
    
    if 'client_id' not in g.json_or_form:
        return jsonify({
            'error': 'client_id is required'
        }), 422
    client_id = g.json_or_form['client_id']
    app_row = query_app_by_client_id(client_id)
    if not app_row:
        return jsonify({
            'error': 'client_id is not found'
        }), 422
    
    if grant_type == 'authorization_code':
        if 'code' not in g.json_or_form:
            return jsonify({
                'error': 'code is required'
            }), 422
        if app_row['authorization_code'] != g.json_or_form['code']:
            return jsonify({
                'error': 'code is invalid'
            }), 422

    if 'client_secret' not in g.json_or_form:
        return jsonify({
            'error': 'client_secret is required'
        }), 422
    if app_row['client_secret'] != g.json_or_form['client_secret']:
        return jsonify({
            'error': 'client_secret is invalid'
        }), 422
    
    if 'redirect_uri' not in g.json_or_form:
        return jsonify({
            'error': 'redirect_uri is required'
        }), 422
    if g.json_or_form['redirect_uri'] not in app_row['redirect_uris']:
        return jsonify({
            'error': 'redirect_uri is not included in the declared list when app is created'
        }), 422

    if 'scope' not in g.json_or_form:
        return jsonify({
            'error': 'scope is required'
        }), 422
    scope_set = set(g.json_or_form['scope'].split(' '))
    app_scope_set = set(app_row['scopes'].split(' '))
    if grant_type == 'authorization_code':
        if scope_set != app_scope_set:
            return jsonify({
                'error': 'scope is not the declared set when app is created'
            }), 422
    else:
        if not scope_set.issubset(app_scope_set):
            return jsonify({
                'error': 'scope is not a subset of the declared set when app is created'
            }), 422

    access_token = random_secret()
    update_app_access_token(client_id, access_token)

    return jsonify({
        'access_token': access_token,
        "token_type": "Bearer",
        "scope": ' '.join(sorted(scope_set)),
        "created_at": int(time.time())
    })


@meta_blueprint.route('/api/v1/accounts/verify_credentials')
@async_token_authenticated
async def verify_credentials():
    user = await g.client.user()  # type: User
    return jsonify({ 
        'id': user.id,
        'username': user.screen_name,
        'acct': user.screen_name,
        'url': f'https://twitter.com/{user.screen_name}',
        'display_name': user.name,
        'note': user.description,
        'avatar': user.profile_image_url,
        'avatar_static': user.profile_image_url,
        'header': user.profile_banner_url,
        'header_static': user.profile_banner_url,
        'locked': user.protected,
        'fields': [],
        'emojis': [],
        'bot': False,
        'group': False,
        'discoverable': False,
        'created_at': user.created_at_datetime.isoformat(),
        'last_status_at': None,  # TODO
        'statuses_count': user.statuses_count,
        'followers_count': user.followers_count,
        'following_count': user.following_count
    })
