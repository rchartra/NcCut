"""
Unit tests for GUI functionality
"""

import unittest
import os
import time
import copy
from functools import partial
from kivy.clock import Clock

import functions
from cutview import CutView

os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'


class AppInfo:
    # Class to hold home root for tests to access
    def __init__(self):
        self.home = None

    def hold_home(self, home):
        self.home = home


run_app = AppInfo()


def pause():
    time.sleep(0.000001)


def run_tests(app, *args):
    # Get home root
    Clock.schedule_interval(pause, 0.000001)
    app.stop()
    run_app.hold_home(app.root.get_screen("HomeScreen"))


def get_app():
    # Run app enough to test without fully loading it
    app = CutView()
    p = partial(run_tests, app)
    Clock.schedule_once(p, 0.000001)
    app.run()


class Test(unittest.TestCase):
    # Test cases
    @classmethod
    def setUpClass(cls):
        get_app()

    def test_file_names(self):
        # Test input file name rules
        run_app.home.ids.file_in.text = "*$%&@! "
        run_app.home.go_btn()
        self.assertEqual(run_app.home.children[0].text, "Invalid File Name", "No irregular characters")
        run_app.home.ids.file_in.text = ""
        run_app.home.go_btn()
        self.assertEqual(run_app.home.children[0].text, "Invalid File Name", "No empty file names")

    def test_widget_cleanup(self):
        # Check that viewer window is clean after removing tools
        run_app.home.ids.file_in.text = "support/example.jpg"
        run_app.home.go_btn()

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



