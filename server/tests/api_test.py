"""Test the google stuff."""


from app import Track


def test_track():
    t = Track()
    d = {
        'artist': 'Test Artist',
        'title': 'Test Title',
        'storeId': 'asdf123',
        'albumArtRef': [
            {
                'url': 'http://whatever.com/artwork.jpg'
            }
        ]
    }
    t.populate(d)
    assert t.artist == d['artist']
    assert t.title == d['title']
    assert t.album_art == d['albumArtRef'][0]['url']
