"""GUI."""

import logging
import wx
from ctypes import string_at
from inspect import isclass
from gmusicapi import Mobileclient
from sound_lib.input import Input
from sound_lib.output import Output
from sound_lib.stream import PushStream
from sound_lib.recording import Recording
from wxgoodies.keys import key_to_str
from .accessibility import speech
from . import commands
from .config import config
from .deck import Deck

logger = logging.getLogger(__name__)


class MainFrame(wx.Frame):
    """The main frame."""
    def __init__(self, *args, **kwargs):
        """Initialise the window."""
        self.help_mode = False
        super(MainFrame, self).__init__(*args, **kwargs)
        p = wx.Panel(self)
        s = wx.BoxSizer(wx.VERTICAL)
        self.text = wx.TextCtrl(
            p,
            value='Usage:\n\n',
            style=wx.TE_MULTILINE | wx.TE_READONLY
        )
        self.commands = []
        self.hotkeys = {}  # hotkey: command pares.
        for x in dir(commands):
            cls = getattr(commands, x)
            if isclass(
                cls
            ) and issubclass(
                cls,
                commands.Command
            ) and cls is not commands.Command:
                cmd = cls(self)
                self.text.AppendText(
                    '%s\n%s\n\n' % (
                        cmd.__doc__, ', '.join(
                            cmd.keys
                        )
                    )
                )
                self.commands.append(cmd)
                for key in cmd.keys:
                    self.hotkeys[key] = cmd
        self.text.SetInsertionPoint(0)
        s.Add(self.text, 1, wx.GROW)
        p.SetSizerAndFit(s)
        self.Show(True)
        self.Maximize()
        self.left = Deck('Left Deck')
        self.right = Deck('Right Deck')
        self.master_volume = 100.0
        self.crossfader = 0
        self.input = Input()
        self.output = Output()
        self.text.Bind(wx.EVT_KEY_DOWN, self.on_keydown)
        self.setup_microphone()
        self.google_reset()

    def google_reset(self):
        """Reset Google to the default un-logged in state."""
        self.google_authenticated = False
        self.google_api = Mobileclient(debug_logging=False)

    def google_login(self):
        """Logs into Google. If login fails or anything else happens, an
        exception is raised."""
        api = self.google_api
        if not self.google_authenticated:
            android_id = config.google['android_id'] or api.FROM_MAC_ADDRESS
            self.google_authenticated = api.login(
                config.google['username'], config.google['password'],
                android_id
            )
        if not self.google_authenticated:
            raise RuntimeError('Login failed.')

    def setup_microphone(self):
        """Setup the microphone."""
        self.microphone_recording = Recording(
            channels=1,
            proc=self.microphone_push
        )
        self.microphone_stream = PushStream(chans=1)
        self.microphone_recording.play()
        self.microphone_stream.volume = 0.0
        self.microphone_stream.play()

    def microphone_push(self, handle, buffer, length, user):
        """Push audio from the microphone to the stream."""
        buf = string_at(buffer, length)
        self.microphone_stream.push(buf)
        return True

    def on_close(self, event):
        """About to close, stop the microphone."""
        event.Skip()
        self.microphone_recording = False
        self.microphone_thread.join()
        self.microphone_audio.stop_stream()
        self.microphone_audio.close()

    def on_keydown(self, event):
        """Key was pressed."""
        key = key_to_str(event.GetModifiers(), event.GetKeyCode())
        if key in self.hotkeys:
            cmd = self.hotkeys[key]
            if self.help_mode:
                logger.info('Showing help on %r.', cmd)
                speech.speak(cmd.__doc__ or 'No description available.')
            if key == self.help_mode_key or not self.help_mode:
                logger.info('Running %r.', cmd)
                cmd.run(key)
        else:
            event.Skip()
