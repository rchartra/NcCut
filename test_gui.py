"""
Unit tests for GUI functionality
"""

import unittest
import os
import time
import copy
import json
from functools import partial
from kivy.clock import Clock
from multimarker import marker_find
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
        """
        Test input file name rules
        """
        run_app.home.ids.file_in.text = "*$%&@! "
        run_app.home.go_btn()
        self.assertEqual(run_app.home.children[0].text, "Invalid File Name", "No irregular characters")
        run_app.home.ids.file_in.text = ""
        run_app.home.go_btn()
        self.assertEqual(run_app.home.children[0].text, "Invalid File Name", "No empty file names")

    def test_widget_cleanup(self):
        """
        Check that viewer window is clean after removing tools
        """
        run_app.home.ids.file_in.text = "support/example.jpg"
        run_app.home.go_btn()

        # Run for all tools in sidebar
        og_side = copy.copy(run_app.home.ids.sidebar.children)
        og_img = copy.copy(run_app.home.img.children[0].children)
        for item in run_app.home.ids.sidebar.children:
            if isinstance(item, type(functions.RoundedButton())) and item.text != "Quit":
                # Start tool
                item.dispatch('on_press')
                item.dispatch('on_release')

                # Press again to clear
                item.dispatch('on_press')
                item.dispatch('on_release')

                self.assertListEqual(og_side, run_app.home.ids.sidebar.children, "Sidebar back to original")
                self.assertListEqual(og_img, run_app.home.img.children[0].children, "All Tools removed")

    def test_project_upload(self):
        run_app.home.ids.file_in.text = "support/example.jpg"
        run_app.home.go_btn()

        # Open Transect Marker tool
        run_app.home.ids.sidebar.children[1].dispatch('on_press')
        run_app.home.ids.sidebar.children[1].dispatch('on_release')

        # Project File
        f = open("support/example.json")
        project = json.load(f)

        # Upload Project File
        multi_mark_instance = run_app.home.transect
        multi_mark_instance.upload_data(marker_find(project, []))

        # Check file uploaded properly
        marker1 = multi_mark_instance.children[3]
        self.assertListEqual(marker1.points, [(654.5692875283441, 261.4475706599112, 40),
                                              (739.8380579378293, 282.76476326228254, 40),
                                              (769.9329180823534, 306.5898608766975, 40),
                                              (808.8054457690305, 345.4623885633744, 40),
                                              (838.9003059135546, 385.5888687560733, 40)],
                             "Marker 1 Points Correct")
        marker2 = multi_mark_instance.children[2]
        self.assertListEqual(marker2.points, [(794.4363556359829, 179.9866550286953, 40),
                                              (870.2534117049004, 157.8733470085944, 40),
                                              (916.0595497465381, 143.65764899567236, 40),
                                              (980.819951805405, 151.5552590028513, 40),
                                              (1015.5694358369924, 156.29382500715863, 40),
                                              (1067.693661884373, 191.04330903874586, 40)],
                             "Marker 2 Points Correct")
        marker3 = multi_mark_instance.children[1]
        self.assertListEqual(marker3.points, [(897.1052857293087, 410.5968672383193, 40),
                                              (965.0247317910473, 345.8364651794524, 40),
                                              (993.4561278168912, 284.2351071234569, 40),
                                              (991.8766058154556, 232.1108810760761, 40)],
                             "Marker 3 Points Correct")
