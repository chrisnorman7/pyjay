"""GUI."""

import logging
import wx
from threading import Thread
from inspect import isclass
from gmusicapi import Mobileclient
from sound_lib.output import Output
from sound_lib.stream import PushStream
from pyaudio import PyAudio, paInt16 as microphone_format
from wxgoodies.keys import key_to_str
from . import commands
from .deck import Deck

logger = logging.getLogger(__name__)


class MainFrame(wx.Frame):
    """The main frame."""
    def __init__(self, *args, **kwargs):
        """Initialise the window."""
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
        self.output = Output()
        self.text.Bind(wx.EVT_KEY_DOWN, self.on_keydown)
        self.google_authenticated = False
        self.google_api = Mobileclient()
        self.microphone_audio = PyAudio().open(
            44100,
            1,
            microphone_format,
            input=True,
            output=False
        )
        self.microphone_stream = PushStream(chans=1)
        self.microphone_thread = Thread(target=self.microphone_push)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.microphone_recording = True
        self.microphone_thread.start()

    def microphone_push(self):
        """Push audio from the microphone to the stream."""
        logger.info('Starting microphone.')
        while self.microphone_recording:
            self.microphone_stream.push(
                self.microphone_audio.read(1024)
            )
        logger.info('Microphone closed.')
        self.microphone_stream.stop()

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
            logger.info('Running command %r.', cmd)
            cmd.run(key)
        else:
            event.Skip()
