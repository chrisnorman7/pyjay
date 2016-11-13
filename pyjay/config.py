"""Configuration."""

from simpleconf import Section, Option, validators
from .application import config_dir
import os.path

class Config(Section):
    """The main configuration class."""
    class audio(Section):
        """Audio configuration."""
        title = 'Audio'
        change_master_volume = Option(5.0, title = 'Amount to change the master volume', validator = validators.Float(min = 0.0, max = 100.0))
        change_pan = Option(0.1, title = 'Amount to change the pan', validator = validators.Float(min = 0.0001, max = 2.0))
        change_volume = Option(0.05, title = 'Amount to change deck volumes', validator = validators.Float(min = 0.00001, max = 1.0))
        change_frequency = Option(100.0, title = 'Amount to change frequency', validator = validators.Float(min = 0.0001, max = 199990.0))
        seek_amount = Option(50000, title = 'The amount to seek by', validator = validators.Integer(min = 0))
        crossfade_amount = Option(1, title = 'Amount to crossfade', validator = validators.Integer(min = 0, max = 100))

config = Config(filename = os.path.join(config_dir, 'config.json'))
