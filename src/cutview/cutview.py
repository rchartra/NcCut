"""
Builds app and sets initial window.

Creates the widget tree and sets the initial window size. To load app, run ``CutView().run()``

"""

import kivy
import kivy.uix as ui
from kivy.app import App
from kivy.metrics import dp
import platform
from cutview.homescreen import HomeScreen
from cutview.logger import get_logging_level
import logging


class CutView(App):
    """
    Builds app and widget tree.

    Creates the initial window and ensures font sizes in the app update uniformly
    when the window resizes.

    """
    def on_start(self):
        """
        Sets initial window size according to operating system.
        """

        # Set logger level to suppress or allow dependency debug messages
        logging.getLogger().setLevel(getattr(logging, get_logging_level().upper(), None))
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

        Returns
            Root of widget tree
        """
        root = ui.screenmanager.ScreenManager()
        root.add_widget(HomeScreen(name="HomeScreen"))
        return root
