"""
Main script that builds and runs full app.
"""

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
            win.size = (dp(1000), dp(600))
            win.minimum_width = dp(800)
            win.minimum_height = dp(550)

    def build(self):
        root = ui.screenmanager.ScreenManager()
        root.add_widget(HomeScreen(name="HomeScreen"))
        return root


if __name__ == "__main__":
    CutView().run()