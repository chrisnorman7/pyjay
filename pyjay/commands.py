"""All commands for the PyJay Application."""

import logging
import wx
from simpleconf.dialogs.wx import SimpleConfWxDialog
from attr import attrs, attrib, Factory
from requests import get
from .config import config

logger = logging.getLogger(__name__)


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


def error(msg, title='Error', style=wx.ICON_EXCLAMATION):
    """Show an error."""
    if isinstance(msg, Exception):
        logger.exception(msg)
    else:
        logger.error(msg)
    return wx.MessageBox(str(msg), title, style=style)


@attrs
class Command:
    """
    All commands must derive from this class.

    parent - The frame that is running the show.
    keys - A list of keys that should trigger this command.
    """

    parent = attrib()
    keys = attrib(default=Factory(list))

    def __attrs_post_init__(self):
        self.setup()

    def setup(self):
        """Override to add extras."""
        pass

    def run(self, key):
        """Actually do something with this command."""
        raise NotImplementedError


class MasterVolume(Command):
    """Alter the master volume."""
    def setup(self):
        self.key_up = '='
        self.key_down = '-'
        self.key_full = 'SHIFT+='
        self.key_mute = 'SHIFT+-'
        self.keys = [self.key_up, self.key_down, self.key_full, self.key_mute]

    def run(self, key):
        """Alter the master volume."""
        if key == self.key_up:
            volume = min(
                100.0,
                self.parent.master_volume +
                config.audio['change_master_volume']
            )
        elif key == self.key_down:
            volume = max(
                0.0,
                self.parent.master_volume -
                config.audio['change_master_volume']
            )
        elif key == self.key_full:
            volume = 100.0
        elif key == self.key_mute:
            volume = 0.0
        if volume != self.parent.master_volume:
            logger.info(
                'Changed master volume from %.2f to %.2f.',
                self.parent.master_volume,
                volume
            )
            self.parent.master_volume = volume
            self.parent.output.set_volume(self.parent.master_volume)


class DeckLoad(Command):
    """Load a song onto a deck."""
    def setup(self):
        self.key_left = 'A'
        self.key_right = ';'
        self.keys = [self.key_left, self.key_right]

    def run(self, key):
        """Load a file."""
        if key == self.key_left:
            deck = self.parent.left
        else:
            deck = self.parent.right
        dlg = wx.FileDialog(
            self.parent,
            message='Choose a file to load',
            style=wx.FD_OPEN
        )
        try:
            if dlg.ShowModal() == wx.ID_OK:
                deck.set_stream(dlg.GetPath())
        except Exception as e:
            error(e)
        finally:
            dlg.Destroy()


class PlayPause(Command):
    """Play or pause the deck."""
    def setup(self):
        self.key_left = 'D'
        self.key_right = 'K'
        self.keys = [self.key_left, self.key_right, 'SPACE']

    def run(self, key):
        if key == self.key_left:
            decks = [self.parent.left]
        elif key == self.key_right:
            decks = [self.parent.right]
        else:
            decks = [self.parent.left, self.parent.right]
        for deck in decks:
            deck.play_pause()


class SetPan(Command):
    """Set the pan of each deck."""
    def setup(self):
        self.left_left = 'S'
        self.left_full_left = 'SHIFT+S'
        self.left_right = 'F'
        self.left_full_right = 'SHIFT+F'
        self.right_left = 'J'
        self.right_full_left = 'SHIFT+J'
        self.right_right = 'L'
        self.right_full_right = 'SHIFT+L'
        self.microphone_left = '['
        self.microphone_full_left = 'SHIFT+['
        self.microphone_right = ']'
        self.microphone_full_right = 'SHIFT+]'
        self.keys = [
            self.left_left,
            self.left_full_left,
            self.left_right,
            self.left_full_right,
            self.right_left,
            self.right_full_left,
            self.right_right,
            self.right_full_right,
        ]

    def run(self, key):
        """Change the pan."""
        if key in [
            self.left_left,
            self.left_full_left,
            self.left_right,
            self.left_full_right
        ]:
            deck = self.parent.left
        else:
            deck = self.parent.right
        amount = config.audio['change_pan']
        if key in [self.left_left, self.right_left]:
            amount = -amount
        if key in [self.left_full_left, self.right_full_left]:
            amount = -1.0
        elif key in [self.left_full_right, self.right_full_right]:
            amount = 1.0
        else:
            amount = deck.pan + amount
        deck.set_pan(amount)


class DeckReset(Command):
    """Reset a deck."""
    def setup(self):
        self.key_left = 'Q'
        self.key_right = 'P'
        self.keys = [self.key_left, self.key_right]

    def run(self, key):
        """Reset the deck."""
        if key == self.key_left:
            deck = self.parent.left
        else:
            deck = self.parent.right
        logger.info('Resetting the %s.', deck)
        deck.reset()


class SetVolume(Command):
    """Set the volume of a deck."""
    def setup(self):
        self.left_up = 'E'
        self.left_down = 'X'
        self.right_up = 'I'
        self.right_down = ','
        self.keys = [
            self.left_up,
            self.left_down,
            self.right_up,
            self.right_down
        ]

    def run(self, key):
        """Set the volume."""
        if key in [self.left_up, self.left_down]:
            deck = self.parent.left
        else:
            deck = self.parent.right
        amount = config.audio['change_volume']
        if key in [self.left_down, self.right_down]:
            amount = -amount
        deck.set_volume(deck.volume + amount)


class FullVolume(Command):
    """Set the deck to full volume."""
    def setup(self):
        self.key_left = 'SHIFT+E'
        self.key_right = 'SHIFT+I'
        self.keys = [self.key_left, self.key_right]

    def run(self, key):
        """Set the deck to rull volume."""
        if key == self.key_left:
            deck = self.parent.left
        else:
            deck = self.parent.right
        deck.set_volume(1.0)


class MuteVolume(Command):
    """Mute a deck."""
    def setup(self):
        self.key_left = 'SHIFT+X'
        self.key_right = 'SHIFT+,'
        self.keys = [self.key_left, self.key_right]

    def run(self, key):
        """Set the deck to rull volume."""
        if key == self.key_left:
            deck = self.parent.left
        else:
            deck = self.parent.right
        deck.set_volume(0.0)


class SetFrequency(Command):
    """Set the frequency of a deck."""
    def setup(self):
        self.left_up = 'C'
        self.left_down = 'Z'
        self.right_up = '.'
        self.right_down = 'M'
        self.keys = [
            self.left_up,
            self.left_down,
            self.right_up,
            self.right_down
        ]

    def run(self, key):
        if key in [self.left_up, self.left_down]:
            deck = self.parent.left
        else:
            deck = self.parent.right
        amount = config.audio['change_frequency']
        if key in [self.left_down, self.right_down]:
            amount = -amount
        deck.set_frequency(deck.frequency + amount)


class DeckSeek(Command):
    """Seek through a deck."""
    def setup(self):
        self.left_left = 'W'
        self.left_full = 'SHIFT+W'
        self.left_right = 'R'
        self.right_left = 'U'
        self.right_full = 'SHIFT+U'
        self.right_right = 'O'
        self.keys = [
            self.left_left,
            self.left_full,
            self.left_right,
            self.right_left,
            self.right_full,
            self.right_right
        ]
        self.amount = 1000

    def run(self, key):
        """Seek through the track."""
        if key in [self.left_left, self.left_full, self.left_right]:
            deck = self.parent.left
        else:
            deck = self.parent.right
        absolute = False
        if key in [self.left_full, self.right_full]:
            amount = 0
            absolute = True
        elif key in [self.left_left, self.right_left]:
            amount = -config.audio['seek_amount']
        else:
            amount = config.audio['seek_amount']
        deck.seek(amount, absolute=absolute)


class CrossFade(Command):
    """Crossfade between the two decks."""
    def setup(self):
        self.key_left = 'G'
        self.key_right = 'H'
        self.key_centre = 'Y'
        self.key_cut_left = 'SHIFT+G'
        self.key_cut_right = 'SHIFT+H'
        self.keys = [
            self.key_left,
            self.key_right,
            self.key_centre,
            self.key_cut_left,
            self.key_cut_right
        ]

    def run(self, key):
        """Crossfade."""
        amount = config.audio['crossfade_amount']
        result = self.parent.crossfader
        if key == self.key_left:
            result = max(-100, result - amount)
        elif key == self.key_right:
            result = min(100, result + amount)
        elif key == self.key_cut_left:
            result = -100
        elif key == self.key_cut_right:
            result = 100
        else:
            result = 0
        ratio = 0.01
        left = self.parent.left
        right = self.parent.right
        self.parent.crossfader = result
        logging.info('Crossfading to %d.', result)
        if result < 0:
            left.set_volume(1.0)
            result = 100 + result
            right.set_volume(result * ratio)
        elif result > 0:
            right.set_volume(1.0)
            result = 100 - result
            left.set_volume(result * ratio)
        else:
            for deck in [left, right]:
                deck.set_volume(1.0)


class DeckStop(Command):
    """Stop a deck."""
    def setup(self):
        self.key_left = 'SHIFT+D'
        self.key_right = 'SHIFT+K'
        self.keys = [self.key_left, self.key_right]

    def run(self, key):
        """Stop the deck."""
        if key == self.key_left:
            deck = self.parent.left
        else:
            deck = self.parent.right
        deck.pause()
        deck.seek(0, absolute=True)


class SetOutput(Command):
    """Set the output device to use."""
    def setup(self):
        self.input_key = 'F11'
        self.output_key = 'F12'
        self.keys = [self.input_key, self.output_key]

    def run(self, key):
        """Set the output device."""
        if key == self.input_key:
            attr = 'input'
        else:
            attr = 'output'
        device = getattr(self.parent, attr)
        names = device.get_device_names()
        dlg = wx.SingleChoiceDialog(
            self.parent,
            'Choose a new %s device' % attr,
            '%s Device' % attr.title(),
            names
        )
        if dlg.ShowModal() == wx.ID_OK:
            new_device = dlg.GetSelection()
        else:
            new_device = None
        dlg.Destroy()
        if new_device is not None:
            if attr == 'input':
                positions = {}
                for deck in [self.parent.left, self.parent.right]:
                    positions[deck] = deck.get_position()
            device.free()
            device = device.__class__()
            setattr(self.parent, attr, device)
            if attr == 'output':
                new_device += 1
            else:
                new_device -= 1
            device.set_device(new_device)
            if attr == 'output':
                for deck in [self.parent.left, self.parent.right]:
                    if deck.filename:
                        if deck.url is False:
                            deck.set_stream(deck.filename)
                            deck.seek(positions[deck], absolute=True)
            else:
                self.parent.setup_microphone()
            logger.info(
                'Set %s to %s.',
                attr,
                device.get_device_names()[device.device - 1]
            )


class Config(Command):
    """View and edit program configuration."""
    def setup(self):
        self.keys = ['CTRL+,']

    def run(self, key):
        """Show the configuration."""
        dlg = wx.SingleChoiceDialog(
            self.parent,
            'Choose a configuration page to load',
            'Configuration',
            config.sections
        )
        if dlg.ShowModal() == wx.ID_OK:
            section = getattr(
                config,
                config.sections[dlg.GetSelection()]
            )
            frame = SimpleConfWxDialog(section, parent=self.parent)
            frame.Show(True)
        dlg.Destroy()


class LoadRequest(Command):
    """Load a request from the requests server."""
    def setup(self):
        self.key_left = 'SHIFT+A'
        self.key_right = 'SHIFT+;'
        self.keys = [self.key_left, self.key_right]

    def run(self, key):
        """Load a file."""
        if key == self.key_left:
            deck = self.parent.left
        else:
            deck = self.parent.right
        try:
            response = get(
                '%s/json' % config.requests['url']
            )
            if not response.ok:
                raise RuntimeError(
                    'Could not connect to the requests uRL. Please ensure it '
                    'is correct in your configuration.'
                )
            j = response.json()
            if not j:
                raise RuntimeError('There are no requests to load.')
            requests = []
            for r in j:
                request = '{0[artist]} - {0[title]}'.format(r)
                if r['requested_by']:
                    if r['requested_message']:
                        text = '. {0[requested_by]}: {0[requested_message]}'
                        request += text.format(r)
                    else:
                        request += ' requested by %s' % r['requested_by']
                requests.append(request)
            dlg = wx.SingleChoiceDialog(
                self.parent,
                'Choose a request to load',
                'Requests',
                requests
            )
            if dlg.ShowModal() == wx.ID_OK:
                request = j[dlg.GetSelection()]
            else:
                request = None
            dlg.Destroy()
            response = get(
                '%s/get_url/%d' % (
                    config.requests['url'],
                    request['id']
                ),
                auth=(
                    config.requests['username'],
                    config.requests['password']
                )
            )
            if not response.ok:
                raise RuntimeError(
                    'The get_url endpoint returned a {:d} error code '
                    'for the URL {}.'.format(
                        response.status_code,
                        response.url
                    )
                )
            j = response.json()
            request['played'] = j['track']['played']
            if j['track'] != request:
                raise RuntimeError(
                    'The requested track differs from the one provided by '
                    'get_url.\n\nTrack: %r\nget_url: %r' % (
                        request,
                        j['track']
                    )
                )
            deck.set_stream(j['url'], url=True)
        except Exception as e:
            error(e)


class GoogleSearch(Command):
    """Load a track from Google Play."""

    def setup(self):
        self.key_left = 'CTRL+A'
        self.key_right = 'CTRL+;'
        self.keys = [self.key_left, self.key_right]

    def run(self, key):
        """Run the command."""
        if not self.parent.google_authenticated:
            self.parent.google_authenticated = self.parent.google_api.login(
                config.google['username'],
                config.google['password'],
                self.parent.google_api.FROM_MAC_ADDRESS
            )
        if not self.parent.google_authenticated:
            return error('Login failed.')
        search = wx.GetTextFromUser('Search', caption='Google Search')
        results = self.parent.google_api.search(search)['song_hits']
        if not results:
            return error('No search results.')
        results = [x['track'] for x in results]
        dlg = wx.SingleChoiceDialog(
            self.parent,
            'Select a track',
            'Search Results',
            [
                '{0[artist]} - {0[title]}'.format(
                    result
                ) for result in results
            ]
        )
        if dlg.ShowModal() == wx.ID_OK:
            track = results[dlg.GetSelection()]
        else:
            track = None
        dlg.Destroy()
        if track is not None:
            id = get_id(track)
            url = self.parent.google_api.get_stream_url(id)
            if key == self.key_left:
                deck = self.parent.left
            else:
                deck = self.parent.right
            deck.set_stream(url, url=True)


class Microphone(Command):
    """Toggle the microphone."""

    def setup(self):
        self.keys = ['/']

    def run(self, key):
        if self.parent.microphone_stream.volume:
            logger.info('Microphone muted.')
            self.parent.microphone_stream.volume = 0.0
        else:
            logger.info('Microphone unmuted.')
            self.parent.microphone_stream.volume = 1.0


class MicrophonePan(Command):
    """Change the microphne pan."""

    def setup(self):
        self.left = '['
        self.full_left = 'SHIFT+['
        self.right = ']'
        self.full_right = 'SHIFT+]'
        self.keys = [
            self.left,
            self.full_left,
            self.right,
            self.full_right
        ]

    def run(self, key):
        amount = config.audio['change_pan']
        if key == self.left:
            amount = -amount
        amount = self.parent.microphone_stream.pan + amount
        if key == self.full_left:
            amount = -1.0
        elif key == self.full_right:
            amount = 1.0
        if amount < -1.0:
            amount = -1.0
        elif amount > 1.0:
            amount = 1.0
        logger.info('Setting microphone pan to %f.', amount)
        self.parent.microphone_stream.set_pan(amount)


class ResetMicrophone(Command):
    """Reset the microphone settings."""

    def setup(self):
        self.keys = ['RETURN']

    def run(self, key):
        logger.info('Resetting the microphone.')
        self.parent.microphone_stream.pan = 0.0
