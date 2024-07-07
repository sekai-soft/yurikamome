import os
import sys


def env_or_bust(env: str):
    if env not in os.environ:
        print(f"Environment variable {env} is required")
        sys.exit(1)
    return os.environ[env]


def get_host_url_or_bust():
    host = env_or_bust('HOST')
    scheme = env_or_bust('SCHEME')
    return f"{scheme}://{host}"
