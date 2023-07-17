"""
Main script that builds and runs app.
"""

# Turn off debug messages from kivy and matplotlib
import os
os.environ["KCFG_KIVY_LOG_LEVEL"] = "error"
import matplotlib.pyplot as plt

import kivy
import kivy.uix as ui
from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.metrics import dp
import platform
from homescreen import HomeScreen


class CutView(App):
    # Starts app and initializes window based on OS
    def on_start(self):
        # Kivy has a mobile app emulator that needs to be turned off for computer app
        kivy.config.Config.set('input', 'mouse', 'mouse,disable_multitouch')
        win = kivy.core.window.Window
        if platform.system() == "Darwin":
            win.size = (dp(500), dp(300))
            win.minimum_width = dp(400)
            win.minimum_height = dp(225)
        else:
            win.size = (dp(750), dp(450))
            win.minimum_width = dp(600)
            win.minimum_height = dp(350)

    def build(self):
        root = ui.screenmanager.ScreenManager()
        root.add_widget(HomeScreen(name="HomeScreen"))
        return root


if __name__ == "__main__":
    CutView().run()
