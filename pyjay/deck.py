"""Provides the Deck class."""

import logging
from attr import attrs, attrib, Factory
from sound_lib.stream import FileStream, URLStream

logger = logging.getLogger(__name__)


@attrs
class Deck:
    """An instance of a deck."""
    name = attrib()
    filename = attrib(default=Factory(lambda: None))
    url = attrib(default=Factory(lambda: False))
    stream = attrib(default=Factory(lambda: None))
    paused = attrib(default=Factory(lambda: True))

    def __attrs_post_init__(self):
        self.log_attribute('name')
        self.reset()

    def reset(self):
        """Reset the deck to defaults."""
        self.set_volume(1.0)
        self.set_pan(0.0)
        self.set_frequency(44100.0)

    def play(self):
        """Unpause the deck."""
        logger.info('Playing %s.', self)
        self.paused = False
        if self.stream:
            self.stream.play()
        else:
            logger.info('Not playing with no stream.')

    def pause(self):
        """Pause this deck."""
        logger.info('Pausing %s.', self)
        self.paused = True
        if self.stream:
            self.stream.pause()

    def play_pause(self):
        """Toggles between play and pause."""
        if self.paused:
            self.play()
        else:
            self.pause()

    def set_stream(self, filename, url=False):
        """Load a stream from the provided filename. If url is True, load a
        URL."""
        self.url = url
        if url:
            self.stream = URLStream(
                url=filename.encode()
            )
        else:
            self.stream = FileStream(
                file=filename
            )
        self.filename = filename
        self.log_attribute('filename')
        self.set_volume(self.volume)
        self.set_pan(self.pan)
        self.set_frequency(self.frequency)
        if not self.paused:
            self.play()

    def set_volume(self, value):
        """Normalises value and sets it."""
        if value > 1.0:
            value = 1.0
        elif value < 0.0:
            value = 0.0
        self.volume = value
        self.log_attribute('volume')
        if self.stream:
            self.stream.set_volume(value)

    def set_pan(self, value):
        """Normalises the value and sets it."""
        if value > 1.0:
            value = 1.0
        elif value < -1.0:
            value = -1.0
        self.pan = value
        self.log_attribute('pan')
        if self.stream:
            self.stream.set_pan(value)

    def set_frequency(self, value):
        """Normalises the value and sets it."""
        if value > 200000.0:
            value = 100000.0
        elif value < 100.0:
            value = 10.0
        self.frequency = value
        self.log_attribute('frequency')
        if self.stream:
            self.stream.set_frequency(value)

    def log_attribute(self, attr):
        """Logs the changing of self.attr."""
        logger.info(
            'Setting %s for %s to %r.',
            attr,
            self,
            getattr(
                self,
                attr
            )
        )

    def get_position(self):
        """Get the play position of the stream."""
        if self.stream:
            return self.stream.get_position()
        else:
            return 0

    def seek(self, amount, absolute=False):
        """Set the playback position."""
        if self.stream:
            if not absolute:
                amount = self.stream.get_position() + amount
            if amount < 0:
                amount = 0
            if amount > self.stream.get_length():
                amount = self.stream.get_length() - 1
            self.stream.set_position(amount)

    def __str__(self):
        return self.name
