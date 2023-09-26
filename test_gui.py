"""
Unit tests for GUI functionality
"""

import unittest
import os
import time
import copy
import numpy as np
import json
from functools import partial
import kivy
from kivy.graphics import Line
from kivy.clock import Clock

import functions
from imageview import ImageView
from singletransect import SingleTransect
from multimarker import MultiMarker, Click
from multitransect import MultiTransect
from markerwidth import MarkerWidth
from marker import Marker
from functions import RoundedButton
from cutview import CutView

os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'


class AppInfo:
    def __init__(self):
        self.home = None

    def hold_home(self, home):
        self.home = home


run_app = AppInfo()


def pause():
    time.sleep(0.000001)


def run_tests(app, *args):
    Clock.schedule_interval(pause, 0.000001)
    app.stop()
    run_app.hold_home(app.root.get_screen("HomeScreen"))


def get_app():
    app = CutView()
    p = partial(run_tests, app)
    Clock.schedule_once(p, 0.000001)
    app.run()


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        get_app()

    def test_file_names(self):
        # Test input file name rules
        run_app.home.ids.file_in.text = "\\"
        run_app.home.gobtn()
        self.assertEqual(run_app.home.children[0].text, "Invalid File Name", "Backslashes don't crash GUI")
        run_app.home.ids.file_in.text = "*$%&@! "
        run_app.home.gobtn()
        self.assertEqual(run_app.home.children[0].text, "Invalid File Name", "No irregular characters")
        run_app.home.ids.file_in.text = ""
        run_app.home.gobtn()
        self.assertEqual(run_app.home.children[0].text, "Invalid File Name", "No empty file names")

    def test_widget_cleanup(self):
        # Check that viewer window is clean after removing tools
        run_app.home.ids.file_in.text = "support/example.jpg"
        run_app.home.gobtn()

        # Run for all tools in sidebar
        og_side = copy.copy(run_app.home.ids.sidebar.children)
        og_img = copy.copy(run_app.home.img.children[0].children)
        for item in run_app.home.ids.sidebar.children:
            if type(item) == type(functions.RoundedButton()) and item.text != "Quit":
                # Start tool
                item.dispatch('on_press')
                item.dispatch('on_release')

                # Press again to clear
                item.dispatch('on_press')
                item.dispatch('on_release')

                self.assertListEqual(og_side, run_app.home.ids.sidebar.children, "Sidebar back to original")
                self.assertListEqual(og_img, run_app.home.img.children[0].children, "All Tools removed")



