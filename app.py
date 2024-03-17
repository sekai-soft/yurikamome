import os
import pytz
import sys
from datetime import datetime
from flask import Flask, jsonify, request
from twikit import Client, Tweet, User
from twikit.utils import Endpoint

def env_or_bust(env: str):
    if env not in os.environ:
        print(f"Environment variable {env} is required")
        sys.exit(1)
    return os.environ[env]


TWITTER_USERNAME = env_or_bust('TWITTER_USERNAME')
TWITTER_EMAIL = env_or_bust('TWITTER_EMAIL')
TWITTER_PASSWORD = env_or_bust('TWITTER_PASSWORD')
SAVED_CREDENTIALS_PATH = env_or_bust('SAVED_CREDENTIALS_PATH')


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


# timestamp looks like "Sat Mar 16 23:00:07 +0000 2024"
def _parse_twitter_timestamp(timestamp: str):
    date_object = datetime.strptime(timestamp, '%a %b %d %H:%M:%S %z %Y')
    date_object = date_object.astimezone(pytz.utc)
    return date_object.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _twitter_media_to_media_attachment(media: dict) -> dict:
    if media.get('type', '') == 'photo':
        original_width = media.get('original_info', {}).get('height', 0)
        original_height = media.get('original_info', {}).get('width', 0)
        return {
            'id': media.get('id_str', ''),
            'type': 'image',
            'url': media.get('media_url_https', ''),
            'preview_url': media.get('media_url_https', ''), # TODO
            'remote_url': media.get('media_url_https', ''),
            'meta': {
                'original': {
                    'width': original_width,
                    'height': original_height,
                    'size': f"{original_width}x{original_height}",
                    'aspect': original_width / original_height
                },
                # TODO: "small": {}
            },
            'description': '', # TODO
            'blurhash': '0'
        }
    # TODO: handle video
    return None

def _tweet_to_status(tweet: Tweet) -> dict:
    if isinstance(tweet.user, dict):
        user_dict = tweet.user
        user_id = user_dict.get('rest_id', '0')
        created_at = user_dict.get('legacy', {}).get('created_at', '')
        screen_name = user_dict.get('legacy', {}).get('screen_name', '')
        display_name = user_dict.get('legacy', {}).get('name', '')
        avatar = user_dict.get('legacy', {}).get('profile_image_url_https', '')
        header = user_dict.get('legacy', {}).get('profile_banner_url', '')
    else:
        user = tweet.user  # type: User
        user_id = user.id
        created_at = user.created_at
        screen_name = user.screen_name
        display_name = user.name
        avatar = user.profile_image_url
        header = user.profile_banner_url if user.profile_banner_url else ''
    return {
        'id': tweet.id,
        'uri': f'http://localhost:5000/users/{screen_name}/statuses/{tweet.id}', # TODO
        'created_at': _parse_twitter_timestamp(tweet.created_at),
        'account': {
            'id': user_id, # TODO
            'username': screen_name,
            'acct': screen_name,
            'url': f'http://localhost:5000/@{screen_name}', # TODO
            'display_name': display_name,
            'note': '',
            'avatar': avatar,
            'avatar_static': avatar,
            'header': header,
            'header_static': header,
            'locked': False, # TODO
            'fields': [],
            'emojis': [],
            'bot': False,
            'group': False,
            'discoverable': False,
            'created_at': _parse_twitter_timestamp(created_at),
            'last_status_at': '2023-02-01T00:00:00.000Z', # TODO
            'status_count': 0, # TODO
            'followers_count': 0, # TODO
            'following_count': 0, # TODO
        },
        'content': tweet.full_text,
        'visibility': 'public', # TODO
        'sensitive': tweet.possibly_sensitive,
        'spoiler_text': '',
        'media_attachments': list(filter(lambda _: _, map(_twitter_media_to_media_attachment, tweet.media if tweet.media else []))),
        'mentions': [], # TODO
        'tags': [], # TODO
        'emojis': [], # TODO
        'reblogs_count': tweet.retweet_count,
        'favourites_count': tweet.favorite_count,
        'replies_count': tweet.reply_count,
        'url': f'http://localhost:5000/@{screen_name}/statuses/{tweet.id}',
        'in_reply_to_id': None, # TODO
        'in_reply_to_account_id': None, # TODO
        'reblog': _tweet_to_status(tweet.retweeted_tweet) if tweet.retweeted_tweet else None,
        'poll': None,
        'card': None,
        'language': tweet.lang,
        'text': tweet.full_text,
        'edited_at': None
    }


@app.route('/api/v1/timelines/home')
def _home_timeline():
    tweets = client.get_timeline(timeline_endpoint=Endpoint.HOME_LATEST_TIMELINE)
    statues = []
    for t in tweets:
        statues.append(_tweet_to_status(t))
    return jsonify(statues)


@app.route('/api/v1/instance')
def _instance():
    return jsonify({
        'uri': 'http://localhost:5000',  # TODO
        'title': 'mastodon-api-shim-for-twitter-unofficial-api', # TODO
        'short_description': 'mastodon-api-shim-for-twitter-unofficial-api', # TODO
        'description': 'mastodon-api-shim-for-twitter-unofficial-api', # TODO
        'email': 'admin@localhost:5000', # TODO
        'version': '4.2.7', # TODO
        'urls': {
            'streaming_api': 'wss://localhost:5000', # TODO
        },
        'stats': {
            'user_count': 0, # TODO
            'status_count': 0,
            'domain_count': 0,
        },
        'thumbnail': None,
        'languages': [],
        'registrations': True,
        'approval_required': False,
        'invites_enabled': False,
        'configuration': {}, # TODO
        'contact_account': None,
        'rules': []
    })


@app.route('/api/v1/apps', methods=['POST'])
def _create_app():
    client_name = request.json['client_name']
    redirect_uris = request.json['redirect_uris']
    website = request.json.get('website', None)
    print(redirect_uris)
    return jsonify({
        'id': '0', # TODO
        'name': client_name,
        'website': website,
        "redirect_uri": redirect_uris,
        'client_id': '', # TODO
        'client_secret': '', # TODO
        "vapid_key": "" # TODO
    })


@app.route('/oauth/authorize')
def _oauth_authorize():
    return f"""
<a href='{request.args['redirect_uri']}?code=0'>Just authorize</a>
"""


@app.route('/oauth/token', methods=['POST'])
def _oauth_get_token():
    return jsonify({
        'access_token': '0', # TODO
        "token_type": "Bearer",
        "scope": "read write follow push", # TODO
        "created_at": 1573979017 # TODO
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
