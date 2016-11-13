"""All commands for the PyJay Application."""

import wx, logging
from simpleconf.dialogs.wx import SimpleConfWxDialog
from .config import config

logger = logging.getLogger(__name__)

class Command:
    """All commands must derive from this class."""
    
    def __init__(self, parent):
        """Initialise with the frame that's running the show."""
        self.parent = parent
        self.keys = [] # Hotkeys that initialise this command.
        self.setup()
    
    def run(self, key):
        """Actually do something with this command."""
        raise NotImplementedError

class MasterVolume(Command):
    """Alter the master volume."""
    def setup(self):
        self.key_up = '='
        self.key_down = '-'
        self.keys = [self.key_up, self.key_down]
    
    def run(self, key):
        """Alter the master volume."""
        if key == self.key_up:
            volume = min(100.0, self.parent.master_volume + config.audio['change_master_volume'])
        else:
            volume = max(0.0, self.parent.master_volume - config.audio['change_master_volume'])
        if volume != self.parent.master_volume:
            logger.info('Changed master volume from %.2f to %.2f.', self.parent.master_volume, volume)
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
        dlg = wx.FileDialog(self.parent, message = 'Choose a file to load', style = wx.FD_OPEN)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                deck.set_stream(dlg.GetPath())
        except Exception as e:
            wx.MessageBox(str(e), 'Error', style = wx.ICON_EXCLAMATION)
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
        self.keys = [
            self.left_left,
            self.left_full_left,
            self.left_right,
            self.left_full_right,
            self.right_left,
            self.right_full_left,
            self.right_right,
            self.right_full_right
        ]
    
    def run(self, key):
        """Change the pan."""
        if key in [self.left_left, self.left_full_left, self.left_right, self.left_full_right]:
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
        self.keys=[self.key_left, self.key_right]
    
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
        self.keys=[self.key_left, self.key_right]
    
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
        deck.seek(amount, absolute = absolute)

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
        deck.seek(0, absolute = True)

class SetOutput(Command):
    """Set the output device to use."""
    def setup(self):
        self.keys = ['F12']
    
    def run(self, key):
        """Set the output device."""
        output = self.parent.output
        names = output.get_device_names()
        dlg = wx.SingleChoiceDialog(self.parent, 'Choose a new device for sound output', 'Output Device', names)
        if dlg.ShowModal() == wx.ID_OK:
            device = dlg.GetSelection()
        else:
            device = None
        dlg.Destroy()
        if device is not None:
            positions = {}
            for deck in [self.parent.left, self.parent.right]:
                positions[deck] = deck.get_position()
            output.free()
            output = output.__class__()
            self.parent.output = output
            output.set_device(device + 1)
            for deck in [self.parent.left, self.parent.right]:
                if deck.filename:
                    deck.set_stream(deck.filename)
                    deck.seek(positions[deck], absolute = True)

class Config(Command):
    """View and edit proram configuration."""
    def setup(self):
        self.keys = ['CTRL+,']
    
    def run(self, key):
        """Show the configuration."""
        frame = SimpleConfWxDialog(config.audio, parent = self.parent)
        frame.Show(True)
