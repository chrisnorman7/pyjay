"""All commands for the PyJay Application."""

import logging
import os
import os.path
import webbrowser
import wx
from simpleconf2.dialogs.wx import SimpleConfWxDialog
from attr import attrs, attrib, Factory
from requests import Session
from jinja2 import Environment
from sound_lib.main import BassError
from . import application
from .accessibility import speech
from .config import config

logger = logging.getLogger(__name__)

http = Session()

html_help = """
<html>
<head>
<title>{{ app_name }} Key Commands</title>
</head>
<body>
<h1>Hotkeys for the {{ app_name }} program.</h1>
<dl>
{% for cmd in frame.commands %}
<dt>{{ cmd.__doc__ or 'No description available' }}</dt>
<dd>{{ cmd.keys|join(', ') }}.</dd>
{% endfor %}
</dl>
</body>
</html>
"""


def get_id(d):
    """Get the id from a dictionary d."""
    return d.get('storeId', d.get('nid', d.get('trackId', d.get('id'))))


def error(msg, title='Error', style=wx.ICON_EXCLAMATION):
    """Show an error."""
    if isinstance(msg, Exception):
        logger.exception(msg)
        msg = str(msg)
    else:
        logger.error(msg)
    return wx.MessageBox(msg, title, style=style)


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
        raise NotImplementedError()

    def run(self, key):
        """Actually do something with this command."""
        raise NotImplementedError()


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
                100.0, self.parent.master_volume +
                config.audio['change_master_volume']
            )
        elif key == self.key_down:
            volume = max(
                0.0, self.parent.master_volume -
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
            speech.speak('Master volume %.2f.' % volume)
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
            self.parent, message='Choose a file to load', style=wx.FD_OPEN
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
            speech.speak(
                '%s %s deck.' % ('Pause' if deck.paused else 'Play', deck)
            )


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
            self.left_left, self.left_full_left, self.left_right,
            self.left_full_right, self.right_left, self.right_full_left,
            self.right_right, self.right_full_right
        ]

    def run(self, key):
        """Change the pan."""
        if key in [
            self.left_left, self.left_full_left, self.left_right,
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
        speech.speak('Pan %.1f.' % deck.pan)


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
        speech.speak('Reset %s.' % deck)


class SetVolume(Command):
    """Set the volume of a deck."""

    def setup(self):
        self.left_up = 'E'
        self.left_down = 'X'
        self.right_up = 'I'
        self.right_down = ','
        self.keys = [
            self.left_up, self.left_down, self.right_up, self.right_down
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
        amount += deck.volume
        deck.set_volume(amount)
        speech.speak('Volume %.1f.' % deck.volume)


class FullVolume(Command):
    """Set the deck to full volume."""

    def setup(self):
        self.key_left = 'SHIFT+E'
        self.key_right = 'SHIFT+I'
        self.keys = [self.key_left, self.key_right]

    def run(self, key):
        """Set the deck to full volume."""
        if key == self.key_left:
            deck = self.parent.left
        else:
            deck = self.parent.right
        deck.set_volume(1.0)
        speech.speak('Volume full.')


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
        speech.speak('Volume mute.')


class SetFrequency(Command):
    """Set the frequency of a deck."""

    def setup(self):
        self.left_up = 'C'
        self.left_down = 'Z'
        self.right_up = '.'
        self.right_down = 'M'
        self.keys = [
            self.left_up, self.left_down, self.right_up, self.right_down
        ]

    def run(self, key):
        if key in [self.left_up, self.left_down]:
            deck = self.parent.left
        else:
            deck = self.parent.right
        amount = config.audio['change_frequency']
        if key in [self.left_down, self.right_down]:
            amount = -amount
        amount += deck.frequency
        deck.set_frequency(amount)
        speech.speak('Frequency %.d.' % deck.frequency)


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
            self.left_left, self.left_full, self.left_right, self.right_left,
            self.right_full, self.right_right
        ]

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
            self.key_left, self.key_right, self.key_centre, self.key_cut_left,
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
        try:
            deck.pause()
        except BassError:
            pass
        finally:
            deck.seek(0, absolute=True)
            speech.speak('Stopped %s deck.' % deck)


class SetOutput(Command):
    """Change audio devices."""

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
        with wx.SingleChoiceDialog(
            self.parent, f'Choose a new {attr} device',
            f'{attr.title()} Device', names
        ) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                new_device = dlg.GetSelection()
            else:
                new_device = None
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
                'Set %s to %s.', attr,
                device.get_device_names()[device.device - 1]
            )


class Config(Command):
    """View and edit program configuration."""

    def setup(self):
        self.keys = ['CTRL+,']

    def run(self, key):
        """Show the configuration."""
        with wx.SingleChoiceDialog(
            self.parent, 'Choose a configuration page to load',
            'Configuration', config.sections
        ) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                section = getattr(config, config.sections[dlg.GetSelection()])
                frame = SimpleConfWxDialog(section, parent=self.parent)
                frame.Show(True)


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
            response = http.get(f'{config.requests["url"]}/json')
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
            with wx.SingleChoiceDialog(
                self.parent, 'Choose a request to load', 'Requests', requests
            ) as dlg:
                if dlg.ShowModal() == wx.ID_OK:
                    request = j[dlg.GetSelection()]
                else:
                    request = None
            response = http.get(
                f'{config.requests["url"]}/get_url/{request["id"]}',
                auth=(config.requests['username'], config.requests['password'])
            )
            if not response.ok:
                raise RuntimeError(
                    'The get_url endpoint returned a {:d} error code '
                    'for the URL {}.'.format(
                        response.status_code, response.url
                    )
                )
            j = response.json()
            request['played'] = j['track']['played']
            if j['track'] != request:
                raise RuntimeError(
                    'The requested track differs from the one provided by '
                    'get_url.\n\nTrack: %r\nget_url: %r' % (
                        request, j['track']
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
        api = self.parent.google_api
        try:
            self.parent.google_login()
        except Exception as e:
            return error(e)
        search = wx.GetTextFromUser('Search', caption='Google Search')
        results = api.search(search)['song_hits']
        if not results:
            return error('No search results.')
        results = [x['track'] for x in results]
        with wx.SingleChoiceDialog(
            self.parent, 'Select a track', 'Search Results',
            ['{0[artist]} - {0[album]} - {0[trackNumber]} - {0[title]}'.format(
                result
            ) for result in results
            ]
        ) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                track = results[dlg.GetSelection()]
            else:
                track = None
        if track is not None:
            id = get_id(track)
            try:
                url = api.get_stream_url(id)
            except Exception as e:
                return error(e)
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
            speech.speak('Mic off.')
            self.parent.microphone_stream.volume = 0.0
        else:
            logger.info('Microphone unmuted.')
            speech.speak('Mic on.')
            self.parent.microphone_stream.volume = 1.0


class MicrophonePan(Command):
    """Change the microphone pan."""

    def setup(self):
        self.left = '['
        self.full_left = 'SHIFT+['
        self.right = ']'
        self.full_right = 'SHIFT+]'
        self.keys = [self.left, self.full_left, self.right, self.full_right]

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
        speech.speak('Microphone pan %.1f.' % amount)


class ResetMicrophone(Command):
    """Reset the microphone settings."""

    def setup(self):
        self.keys = ['RETURN']

    def run(self, key):
        logger.info('Resetting the microphone.')
        speech.speak('Reset mic.')
        self.parent.microphone_stream.pan = 0.0


class Help(Command):
    """Show help in your web browser or enable help mode."""

    def setup(self):
        self.help_html_key = 'F1'
        self.parent.help_mode_key = 'SHIFT+/'
        self.keys = [self.help_html_key, self.parent.help_mode_key]
        self.environment = Environment()
        self.environment.globals.update(
            app_name=application.name,
            frame=self.parent
        )

    def run(self, key):
        """Generate HTML."""
        if key == self.help_html_key:
            html = self.environment.from_string(html_help).render()
            if not os.path.isdir(application.config_dir):
                os.makedirs(application.config_dir)
            path = os.path.join(application.config_dir, 'hotkeys.html')
            with open(path, 'w') as f:
                f.write(html)
            webbrowser.open(path)
        else:
            self.parent.help_mode = not self.parent.help_mode
            speech.speak('Help mode %s.' % (
                'enabled' if self.parent.help_mode else 'disabled')
            )


class SpeakProgress(Command):
    """Speak the position of a deck."""

    def setup(self):
        self.left = 'SHIFT+R'
        self.right = 'SHIFT+O'
        self.keys = [self.left, self.right]

    def run(self, key):
        if key == self.left:
            deck = self.parent.left
        else:
            deck = self.parent.right
        s = deck.stream
        if s is None:
            speech.speak('Nothing playing.')
        else:
            speech.speak(
                '%.2f%%' % (s.get_position() * (100 / s.get_length()))
            )


class ResetFrequency(Command):
    """Reset the frequency of a deck."""

    def setup(self):
        self.key_left = 'SHIFT+Q'
        self.key_right = 'SHIFT+P'
        self.keys = [self.key_left, self.key_right]

    def run(self, key):
        if key == self.key_left:
            deck = self.parent.left
        else:
            deck = self.parent.right
        deck.set_frequency(44100.0)
        speech.speak('Reset frequency.')


class ResetPan(Command):
    """Reset the pan of a deck."""

    def setup(self):
        self.key_left = 'SHIFT+T'
        self.key_right = 'SHIFT+Y'
        self.keys = [self.key_left, self.key_right]

    def run(self, key):
        if key == self.key_left:
            deck = self.parent.left
        else:
            deck = self.parent.right
        deck.set_pan(0.0)
        speech.speak('Reset pan.')


class RegisteredDevices(Command):
    """Allows you to set the ID of the device you use to sign into Google.."""

    def setup(self):
        self.keys = ['F8']

    def run(self, key):
        api = self.parent.google_api
        try:
            self.parent.google_login()
        except Exception as e:
            return error(e)
        devices = api.get_registered_devices()
        with wx.SingleChoiceDialog(
            self.parent, 'Select a device name to login with its ID',
            'Registered Devices',
            [d.get('friendlyName', 'Unnamed') for d in devices]
        ) as dlg:
            res = dlg.ShowModal()
        if res == wx.ID_OK:
            index = dlg.GetSelection()
            device = devices[index]
            id = device['id']
            if id.startswith('0x'):
                id = id[2:]
            config.google['android_id'] = id
            self.parent.google_reset()
            try:
                self.parent.google_login()
            except Exception as e:
                error(e)


class OpenFile(Command):
    """Open the file loaded to a deck externally."""

    def setup(self):
        self.key_left = 'SHIFT+C'
        self.key_right = 'SHIFT+.'
        self.keys = [self.key_left, self.key_right]

    def run(self, key):
        if key == self.key_left:
            deck = self.parent.left
        else:
            deck = self.parent.right
        filename = deck.filename
        if filename is None:
            error('Nothing loaded.')
        else:
            webbrowser.open(filename)


class SpeakPlayState(Command):
    """Speak the play state of a deck."""

    def setup(self):
        self.key_left = 'SHIFT+Z'
        self.key_right = 'SHIFT+M'
        self.keys = [self.key_left, self.key_right]

    def run(self, key):
        if key == self.key_left:
            deck = self.parent.left
        else:
            deck = self.parent.right
        speech.speak('Paused.' if deck.paused else 'Not paused.')
