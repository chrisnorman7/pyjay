"""App-specific storage."""

import wx

name = 'PyJay'
__version__ = '0.2'

app = wx.App()
app.SetAppName('{} V{}'.format(name, __version__))

config_dir = wx.StandardPaths.Get().GetUserDataDir()
