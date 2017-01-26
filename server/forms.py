"""Provides various forms used by the web pages."""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, validators


class SearchForm(FlaskForm):
    """Search for tracks."""
    search = StringField(
        'Song, artist or album',
        validators=[
            validators.DataRequired(),
            validators.Length(min=2)
        ]
    )


class RequestForm(FlaskForm):
    """Request a song."""
    name = StringField('Your name')
    message = TextAreaField('Message')
