"""
Builds app and file settings menu.
"""

# Turn off debug messages from kivy and matplotlib
import os
os.environ["KCFG_KIVY_LOG_LEVEL"] = "info"
import matplotlib.pyplot as plt

import kivy
import kivy.uix as ui
from kivy.uix.settings import SettingsWithSidebar
from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.metrics import dp
import platform
import json
from homescreen import HomeScreen


set_config = json.dumps([
    {'type': 'title',
     'title': 'Configurations'},
    {'type': 'string',
     'title': 'Output Destination',
     'desc': 'Directory plots and data are saved to',
     'section': 'main',
     'key': 'output'}])


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
        win.bind(on_resize=self.on_resize)

    def on_resize(self, *args):
        self.root.get_screen("HomeScreen").font_adapt()

    def build(self):
        # Build app
        self.use_kivy_settings = False
        self.settings_cls = SettingsWithSidebar
        root = ui.screenmanager.ScreenManager()
        root.add_widget(HomeScreen(name="HomeScreen"))
        return root

    def build_config(self, config):
        # Set default values for settings
        config.setdefaults('main', {
            'output': os.getcwd()
        })

    def build_settings(self, settings):
        # Load Settings panel
        settings.add_json_panel('App Settings',
                                self.config,
                                data=set_config)

    def on_config_change(self, config, section, key, value):
        # Triggered on setting change
        if key == "output" and not os.path.isdir(value):
            config.set('main', 'output', os.getcwd())
            config.write()
            self.close_settings()
            self.destroy_settings()
            self.open_settings()
        else:
            self.root.get_screen("HomeScreen").update_settings(key, value)

        # Don't overwrite defaults
        os.remove('cutview.ini')


if __name__ == "__main__":
    CutView().run()
