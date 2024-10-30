# SPDX-FileCopyrightText: 2024 University of Washington
#
# SPDX-License-Identifier: BSD-3-Clause

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
import nccut.functions as func


class NcCut(App):
    """
    Builds app and widget tree.

    Creates the initial window and ensures font sizes in the app update uniformly
    when the window resizes.

    """
    def __init__(self, file=None, config=None, **kwargs):
        """
        Initialize app with file if included via command line
        """
        super(NcCut, self).__init__(**kwargs)
        self.file = file
        self.config_file = config
        self.btn_img_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "__btn_images__")
        default_config = {"graphics_defaults": {"contrast": 0, "line_color": "Blue", "colormap": "viridis",
                                                "circle_size": 5},
                          "netcdf": {"dimension_order": ["z", "y", "x"]},
                          "tool_defaults": {"marker_width": 40},
                          "metadata": {}}
        config_dict = func.find_config(self.config_file)
        if config_dict:
            for k in config_dict.keys():
                for s in config_dict[k].keys():
                    default_config[k][s] = config_dict[k][s]
        self.general_config = default_config
        img_names = {"Blue": "blue_line_btn.png", "Green": "green_line_btn.png", "Orange": "orange_line_btn.png"}
        self.default_line_btn_img = img_names[self.general_config["graphics_defaults"]["line_color"]]

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
        home = HomeScreen(name="HomeScreen", btn_img_path=self.btn_img_path, file=self.file, conf=self.general_config)
        root.add_widget(home)
        return root


def run():
    """
    Runs app with command line. Can also specify file to load and configuration file
    """
    bar.next()
    parser = argparse.ArgumentParser()
    parser.add_argument('-file', nargs='?', default=None, help="File path for image or NetCDF file")
    parser.add_argument('-config', nargs='?', default=None, help="File path for config file: 'nccut_config.toml'")
    args = parser.parse_args()
    file = args.file
    config = args.config
    if file:
        if not os.path.isfile(file):
            print("ERROR: File Not Found")
            return
        elif len(re.findall(r'[^A-Za-z0-9_:\\.\-/]', str(file))) > 0:
            print("ERROR: Invalid File Name")
            return
        elif not os.path.splitext(file)[1] in [".jpg", ".jpeg", ".png", ".nc"]:
            print("ERROR: File not an Image or NetCDF File")
            return
    if config:
        print(config)
        if not os.path.isfile(config):
            print("ERROR: Config File Not Found")
            return
        elif len(re.findall(r'[^A-Za-z0-9_:\\.\-/]', str(file))) > 0:
            print("ERROR: Invalid Config File Path")
            return
        elif not os.path.basename(config) == "nccut_config.toml":
            print("ERROR: File Passed is not NcCut Config File (file must be named 'nccut_config.toml)")
            return
    bar.next()
    bar.finish()
    NcCut(file=file, config=config).run()
