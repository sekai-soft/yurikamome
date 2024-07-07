import pytz
from datetime import datetime
from twikit import Tweet, User


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

def _tweet_to_status(tweet: Tweet, host_url: str) -> dict:
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
        'uri': f'{host_url}/users/{screen_name}/statuses/{tweet.id}', # TODO
        'created_at': _parse_twitter_timestamp(tweet.created_at),
        'account': {
            'id': user_id, # TODO
            'username': screen_name,
            'acct': screen_name,
            'url': f'{host_url}/@{screen_name}', # TODO
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
        'url': f'{host_url}/@{screen_name}/statuses/{tweet.id}',
        'in_reply_to_id': None, # TODO
        'in_reply_to_account_id': None, # TODO
        'reblog': _tweet_to_status(tweet.retweeted_tweet, host_url) if tweet.retweeted_tweet else None,
        'poll': None,
        'card': None,
        'language': tweet.lang,
        'text': tweet.full_text,
        'edited_at': None
    }
