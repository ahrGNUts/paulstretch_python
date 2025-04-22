#!/usr/bin/env python
"""
Runner script for the Paulstretch GUI application
"""

import paulstretch_gui

if __name__ == "__main__":
    paulstretch_gui.app = paulstretch_gui.wx.App(False)
    paulstretch_gui.frame = paulstretch_gui.PaulstretchFrame()
    paulstretch_gui.app.MainLoop() 