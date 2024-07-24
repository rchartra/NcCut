"""
Builds app and sets initial window.

Creates the widget tree and sets the initial window size. To load app, run ``NcCut().run()``

"""

from progress.bar import ChargingBar
bar = ChargingBar("Loading App", max=3)
import os
import re
import logging
import copy
from nccut.logger import get_logging_level
_LOG_LEVEL_ = copy.copy(get_logging_level())
os.environ["KIVY_NO_ARGS"] = "true"
os.environ["KCFG_KIVY_LOG_LEVEL"] = _LOG_LEVEL_.lower()
bar.next()
from kivy.metrics import dp
import kivy
import kivy.uix as ui
from kivy.app import App
import platform
import argparse
logging.getLogger().setLevel(getattr(logging, _LOG_LEVEL_, None))
bar.next()
from nccut.homescreen import HomeScreen


class NcCut(App):
    """
    Builds app and widget tree.

    Creates the initial window and ensures font sizes in the app update uniformly
    when the window resizes.

    """
    def __init__(self, file=None, **kwargs):
        """
        Initialize app with file if included via command line
        """
        super(NcCut, self).__init__(**kwargs)
        self.file = file

    def on_start(self):
        """
        Sets initial window size according to operating system.
        """

        # Set logger level to suppress or allow dependency debug messages
        logging.getLogger().setLevel(getattr(logging, get_logging_level().upper(), None))
        # Kivy has a mobile app emulator that needs to be turned off for computer app
        kivy.config.Config.set('input', 'mouse', 'mouse,disable_multitouch')
        kivy.config.Config.set('kivy', 'exit_on_escape', '0')
        win = kivy.core.window.Window
        logging.getLogger("kivy").setLevel(logging.ERROR)
        if platform.system() == "Darwin":  # macOS
            win.size = (dp(500), dp(300))
            win.minimum_width, win.minimum_height = (dp(400), dp(225))
        else:
            win.size = (dp(750), dp(450))
            win.minimum_width, win.minimum_height = (dp(600), dp(350))
        logging.getLogger("kivy").setLevel(_LOG_LEVEL_)

        win.bind(on_resize=self.on_resize, on_maximize=self.on_resize, on_restore=self.on_resize)

    def on_resize(self, *args):
        """
        Triggers font adjustments when the window size is adjusted.

        Args:
            *args: Accepts args App class supplies though they aren't needed.
        """
        self.root.get_screen("HomeScreen").font_adapt()

    def build(self):
        """
        Override App class build method and return widget tree.

        Returns
            Root of widget tree
        """
        root = ui.screenmanager.ScreenManager()
        home = HomeScreen(name="HomeScreen", file=self.file)
        root.add_widget(home)
        return root


def run():
    """
    Runs app with command line file entry
    """
    bar.next()
    parser = argparse.ArgumentParser()
    parser.add_argument('file', nargs='?', default=None, help="File path for image or NetCDF file")
    args = parser.parse_args()
    file = args.file
    if not file:
        bar.next()
        bar.finish()
        NcCut().run()
    elif not os.path.isfile(file):
        print("ERROR: File Not Found")
    elif len(re.findall(r'[^A-Za-z0-9_:\\.\-/]', str(file))) > 0:
        print("ERROR: Invalid File Name")
    elif not os.path.splitext(file)[1] in [".jpg", ".jpeg", ".png", ".nc"]:
        print("ERROR: File not an Image or NetCDF File")
    else:
        bar.next()
        bar.finish()
        NcCut(file).run()
