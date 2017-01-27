"""Web pages."""

from datetime import datetime
from flask import (
    render_template, flash, redirect, url_for, jsonify, abort, request)
from attr import attrs, attrib, Factory, asdict
from gmusicapi import CallFailure
from app import app, get_id, Track, basic_auth
from api import api
from forms import SearchForm, RequestForm


@attrs
class TrackTemplate:
    """A track which can be rendered by the templating engine."""
    id = attrib()
    artist = attrib()
    album = attrib()
    title = attrib()
    artwork_url = attrib(default=Factory(lambda: None))


@app.route('/', methods=['POST', 'GET'])
def index():
    """The home page."""
    form = SearchForm()
    tracks = []
    if form.validate_on_submit():
        search = form.data['search']
        results = api.search(search)['song_hits']
        for result in results:
            result = result['track']
            track = TrackTemplate(
                get_id(result),
                result.get('artist', 'Unknown Artist'),
                result.get('album', 'Unknown Album'),
                result.get('title', 'Untitled Track')
            )
            if result.get('albumArtRef', []):
                track.artwork_url = result['albumArtRef'][0]['url']
            tracks.append(track)
    return render_template(
        'index.html',
        form=form,
        tracks=tracks
    )


@app.route('/request_track/<id>', methods=['GET', 'POST'])
def request_track(id):
    """Request a track."""
    if Track.query.filter_by(
        google_id=id,
        played=None
    ).count():
        flash('That track has already been requested.')
        return redirect(url_for('index'))
    form = RequestForm()
    if form.validate_on_submit():
        try:
            track = Track()
            track.requested_by = form.data['name']
            track.requested_message = form.data['message']
            track.populate(api.get_track_info(id))
            flash(
                'Thank you for requesting {0.title} by {0.artist}.'.format(
                    track
                )
            )
        except CallFailure:
            flash('Could not find a track with that ID.')
        return redirect(url_for('index'))
    else:
        return render_template(
            'request_track.html',
            form=form
        )


@app.route('/json')
def get_json():
    """Return the request queue as json."""
    requests = []
    for track in Track.query.filter_by(played=None):
        requests.append(asdict(track))
    return jsonify(requests)


@app.route('/get_url/<int:id>')
@basic_auth.required
def get_url(id):
    """Get the URL for the track with the given id."""
    track = Track.query.filter_by(id=id, played=None)
    if track.count():
        track = track.first()
        track.played = datetime.now()
        track.save()
        url = api.get_stream_url(track.google_id)
        d = dict(
            track=asdict(track),
            url=url
        )
        track.delete()
        return jsonify(d)
    abort(404)


@app.route('/requests')
def requests():
    """Show all the requests."""
    return render_template(
        'requests.html',
        requests=Track.query.filter_by(
            played=None
        )
    )


@app.route('/played')
def played():
    """Show all the tracks that have played."""
    return render_template(
        'played.html',
        requests=Track.query.filter(
            Track.played.isnot(None)
        )
    )


@app.route('/delete/<int:id>')
@basic_auth.required
def delete(id):
    """Delete a request."""
    track = Track.query.filter_by(id=id, played=None)
    if track.count():
        track = track.first()
        track.delete()
        flash(
            '{0.artist} - {0.title} was removed from the requests queue.'.
            format(track)
        )
    else:
        flash('There is no track with that id.')
    if request.referrer is None:
        url = url_for('index')
    else:
        url = request.referrer
    return redirect(url)
