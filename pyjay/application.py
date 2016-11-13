"""App-specific storage."""

name = 'PyJay'
__version__ = '0.1'

import wx

app = wx.App()
app.SetAppName('{} V{}'.format(name, __version__))

config_dir = wx.StandardPaths.Get().GetUserDataDir()
