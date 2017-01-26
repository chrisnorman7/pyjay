"""The google music api."""

from gmusicapi import Mobileclient
from app import config

api = Mobileclient()

api.login(
    config['google_username'],
    config['google_password'],
    config['android_id'] or api.FROM_MAC_ADDRESS
)
