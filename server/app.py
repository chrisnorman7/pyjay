"""The flask application."""

from os import urandom
from getpass import getpass
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_basicauth import BasicAuth
from configobj import ConfigObj
from attrs_sqlalchemy import attrs_sqlalchemy


def get_id(d):
    """Get the id from a dictionary d."""
    return d.get(
        'storeId',
        d.get(
            'nid',
            d.get(
                'trackId',
                d.get(
                    'id'
                )
            )
        )
    )


app = Flask('Pyjay Server')

app.config['SECRET_KEY'] = urandom(64)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_DATABASE_ECHO'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

config = ConfigObj('config.ini')

if 'google_username' not in config:
    config['google_username'] = input('Google Username: ')
if 'google_password' not in config:
    config['google_password'] = getpass()
if 'android_id' not in config:
    config['android_id'] = ''
if 'basic_auth_username' not in config:
    config['basic_auth_username'] = 'admin'
if 'basic_auth_password' not in config:
    config['basic_auth_password'] = 'password'

app.config['BASIC_AUTH_USERNAME'] = config['basic_auth_username']
app.config['BASIC_AUTH_PASSWORD'] = config['basic_auth_password']

basic_auth = BasicAuth(app)

db = SQLAlchemy(app)


@attrs_sqlalchemy
class Track(db.Model):
    """A track to be played."""

    id = db.Column(db.Integer, primary_key=True)
    artist = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    album_art = db.Column(db.String(1000))
    requested_by = db.Column(db.String(50), nullable=True)
    requested_message = db.Column(db.String(500), nullable=True)
    google_id = db.Column(db.String(30), unique=True, nullable=False)
    played = db.Column(db.DateTime, default=None)

    def populate(self, data):
        """"Populate from a dictionary."""
        self.title = data.get('title', 'Unknown Song')
        self.artist = data.get('artist', 'Unknown Artist')
        self.google_id = get_id(data)
        artwork = data.get('albumArtRef', [])
        if artwork:
            self.album_art = artwork[0]['url']
        self.save()

    def save(self):
        """Save this object to the database."""
        db.session.add(self)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

    def delete(self):
        """Delete this track."""
        db.session.delete(self)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e


db.create_all()
