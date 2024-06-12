"""
Builds app and file settings menu.

File to run to start up the GUI. Initializes the settings in the 'File' menu
and sets the initial window size.

Usage from command line:

python cutview.py

"""

# Turns off debug messages from kivy and matplotlib
import os
import logging
logging.getLogger('matplotlib.font_manager').disabled = True
# os.environ["KIVY_NO_CONSOLELOG"] = "1"

import kivy
import kivy.uix as ui
from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.metrics import dp
import platform
from homescreen import HomeScreen


class CutView(App):
    """
    Builds GUI and manages setting changes.

    Defines callbacks to various events that should trigger some change to the
    GUI's settings. On GUI start it sets the initial settings and builds the app.

    Attributes:
        Inherits attributes from kivy.app.App (see kivy docs)
    """
    def on_start(self):
        """
        Sets initial window size according to operating system.
        """

        # Kivy has a mobile app emulator that needs to be turned off for computer app

        kivy.config.Config.set('input', 'mouse', 'mouse,disable_multitouch')

        win = kivy.core.window.Window
        if platform.system() == "Darwin":  # macOS
            win.size = (dp(500), dp(300))
            win.minimum_width = dp(400)
            win.minimum_height = dp(225)
        else:
            win.size = (dp(750), dp(450))
            win.minimum_width = dp(600)
            win.minimum_height = dp(350)
        win.bind(on_resize=self.on_resize)

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
        """
        root = ui.screenmanager.ScreenManager()
        root.add_widget(HomeScreen(name="HomeScreen"))
        return root


if __name__ == "__main__":
    CutView().run()
