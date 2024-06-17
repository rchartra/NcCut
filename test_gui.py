"""
Unit tests for GUI functionality
"""

import unittest
import os
import time
import copy
import json
import xarray as xr
import numpy as np
from functools import partial
from kivy.clock import Clock
from kivy.uix.button import Button
from multimarker import Click, marker_find
from markerwidth import MarkerWidth
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
        """
        Tests the project upload function of the Transect Marker tool.

        Assumes 'support/example.json' exists and is a valid project file for 'support/example.jpg' with
        a variable 'Vorticity' and three markers.
        """
        run_app.home.ids.file_in.text = "support/example.jpg"
        run_app.home.go_btn()

        # Open Transect Marker tool
        sidebar = run_app.home.ids.sidebar
        tm_but = next((but for but in sidebar.children if but.text == "Transect Marker"), None)
        tm_but.dispatch('on_press')
        tm_but.dispatch('on_release')

        # Project File
        f1 = open("support/example.json")
        project1 = json.load(f1)

        # Upload Project File
        multi_mark_instance = run_app.home.transect
        multi_mark_instance.upload_data(marker_find(project1, []))

        # Check file uploaded properly
        for i, mar in enumerate(list(project1["Vorticity"].keys())):
            p_m = project1["Vorticity"][mar]
            m_expected_points = list(zip(p_m["Click X"], p_m["Click Y"], p_m["Width"]))
            marker = multi_mark_instance.children[len(list(project1["Vorticity"].keys())) - i]
            self.assertListEqual(marker.points, m_expected_points, mar + " Points Correct")

        # Test out of bounds project files don't get uploaded.
        run_app.home.ids.file_in.text = "support/example.nc"
        run_app.home.go_btn()
        vals = {'x': 'x', 'y': 'y',
                'z': 'Select...', 'z_val': 'Select...',
                'var': 'Vorticity', 'file': xr.open_dataset("support/example.nc")}
        run_app.home.nc_open(vals)
        tm_but.dispatch('on_press')
        tm_but.dispatch('on_release')

        # Load File
        f2 = open("support/test_project_file.json")
        project2 = json.load(f2)

        # Upload Project File
        multi_mark_instance = run_app.home.transect
        multi_mark_instance.upload_data(marker_find(project2, []))

        self.assertEqual(len(multi_mark_instance.children), 1, "Project files that don't fit in file bounds fail")
        self.assertEqual(multi_mark_instance.children[0].points, [], "Empty new marker loaded")

    def test_marker_transect(self):
        """
        Test marker and marker point deletion.
        """
        run_app.home.ids.file_in.text = "support/example.jpg"
        run_app.home.go_btn()

        # Open Transect Marker tool
        sidebar = run_app.home.ids.sidebar
        tm_but = next((but for but in sidebar.children if but.text == "Transect Marker"), None)
        tm_but.dispatch('on_press')
        tm_but.dispatch('on_release')

        # Project File
        f = open("support/example.json")
        project = json.load(f)

        # Upload Project File
        multi_mark_instance = run_app.home.transect
        multi_mark_instance.upload_data(marker_find(project, []))

        # Open editing mode
        e_but = next((but for but in sidebar.children if but.text == "Edit Mode"), None)
        e_but.dispatch('on_press')
        e_but.dispatch('on_release')

        # Delete last clicked point
        dp_but = next((but for but in sidebar.children if but.text == "Delete Last Point"), None)
        dp_but.dispatch('on_press')
        dp_but.dispatch('on_release')

        # Check last clicked point was properly deleted
        m3 = project["Vorticity"]["Marker 3"]
        m3_expected_points = list(zip(m3["Click X"][:-1], m3["Click Y"][:-1], m3["Width"][:-1]))
        self.assertEqual(len(multi_mark_instance.children), 3, "Deleted fourth empty marker")
        self.assertEqual(multi_mark_instance.children[0].points, m3_expected_points, "Only the last point was deleted")

        # Delete most recent marker
        dl_but = next((but for but in sidebar.children if but.text == "Delete Last Line"), None)
        dl_but.dispatch('on_press')
        dl_but.dispatch('on_release')

        # Check most recent marker was properly deleted
        self.assertEqual(len(multi_mark_instance.children), 2, "Last marker deleted")

        # Add new line
        b_but = next((but for but in sidebar.children if but.text == "Back"), None)
        b_but.dispatch('on_press')
        b_but.dispatch('on_release')
        n_but = next((but for but in sidebar.children if but.text == "New Line"), None)
        n_but.dispatch('on_press')
        n_but.dispatch('on_release')
        self.assertEqual(len(multi_mark_instance.children), 3, "New marker created")

        # Delete point
        e_but.dispatch('on_press')
        e_but.dispatch('on_release')
        dp_but.dispatch('on_press')
        dp_but.dispatch('on_release')
        self.assertEqual(len(multi_mark_instance.children), 2, "Empty marker deleted")
        m2 = project["Vorticity"]["Marker 2"]
        m2_expected_points = list(zip(m2["Click X"][:-1], m2["Click Y"][:-1], m2["Width"][:-1]))
        self.assertEqual(multi_mark_instance.children[0].points, m2_expected_points, "Last point of m2 was deleted")

        # Test width adjustments
        b_but.dispatch('on_press')
        b_but.dispatch('on_release')
        n_but.dispatch('on_press')
        n_but.dispatch('on_release')

        # Simulate marker press with width changes
        x = run_app.home.size[0]
        y = run_app.home.size[1]

        incs = np.linspace(0.4, 0.8, 10)
        x_arr = incs * x
        y_arr = incs * y
        w_arr = [int(n * 100) for n in incs]
        multi_mark_instance.on_touch_down(Click(float(x_arr[0]), float(y_arr[0])))
        w_wid = next((but for but in sidebar.children if isinstance(but, MarkerWidth)), None)
        for i in range(1, len(incs)):
            w_wid.txt.text = str(w_arr[i])
            w_wid.btn.dispatch('on_press')
            w_wid.btn.dispatch('on_release')
            multi_mark_instance.on_touch_down(Click(float(x_arr[i]), float(y_arr[i])))
        self.assertEqual(multi_mark_instance.children[0].points, list(zip(x_arr, y_arr, w_arr)),
                         "Points were selected with appropriate width adjustments")

        # Test Drag Mode
        d_but = next((but for but in sidebar.children if isinstance(but, Button) and but.text == "Drag Mode"), None)
        d_but.dispatch('on_press')
        d_but.dispatch('on_release')
        multi_mark_instance.on_touch_down(Click(0.43 * x, 0.43 * y))
        self.assertEqual(multi_mark_instance.children[0].points, list(zip(x_arr, y_arr, w_arr)),
                         "No new point was added")

    def test_multi_transect(self):

        run_app.home.ids.file_in.text = "support/example.jpg"
        run_app.home.go_btn()

        # Open Transect Marker tool
        sidebar = run_app.home.ids.sidebar
        tm_but = next((but for but in sidebar.children if but.text == "Transect"), None)
        tm_but.dispatch('on_press')
        tm_but.dispatch('on_release')

        x = run_app.home.size[0]
        y = run_app.home.size[1]
        incs = [0.5, 0.55, 0.6, 0.65]
        x_arr = incs * x
        y_arr = incs * y

        tran_instance = run_app.home.transect

        # First Click
        tran_instance.on_touch_down(Click(x_arr[0], y_arr[0]))
        self.assertIsNone(next((but for but in sidebar.children if but.text == "Plot"), None),
                          "No Plot Button on First Click")
        self.assertEqual(len(tran_instance.children), 1, "Transect Added")

        # Second Click
        tran_instance.on_touch_down(Click(x_arr[1], y_arr[1]))
        self.assertIsInstance(next((but for but in sidebar.children if but.text == "Plot")), Button,
                              "Plot Button added")
        self.assertEqual(len(tran_instance.children), 1, "Only one transect")
