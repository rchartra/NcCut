"""
Unit tests for GUI functionality
"""

import unittest
import os
import time
import copy
import pooch
import json
import cv2
import numpy as np
from functools import partial
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.uix.button import Button
from cutview.multimarker import Click, marker_find
from cutview.markerwidth import MarkerWidth
import cutview.functions as functions
from cutview.cutview import CutView

os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'
SUPPORT_FILE_PATH = "support/"
TEST_NC_PATH = pooch.retrieve(url="doi:10.5281/zenodo.12208969/test_nc.nc", known_hash=None)


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


def load_nc(variable):
    run_app.home.ids.file_in.text = SUPPORT_FILE_PATH + "example.nc"
    run_app.home.go_btn()
    popup = run_app.home.nc_popup
    popup.var_select.text = variable
    popup.x_select.text = "x"
    popup.y_select.text = "y"
    popup.go.dispatch("on_press")
    popup.go.dispatch("on_release")


def select_sidebar_button(text):
    sidebar = run_app.home.ids.sidebar
    but = next((but for but in sidebar.children if isinstance(but, Button) and but.text == text), None)
    but.dispatch('on_press')
    but.dispatch('on_release')


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
        run_app.home.ids.file_in.text = ""
        run_app.home.go_btn()
        self.assertEqual(run_app.home.children[0].text, "Invalid File Name", "No empty file names")
        run_app.home.ids.file_in.text = SUPPORT_FILE_PATH + "example.json"
        run_app.home.go_btn()
        self.assertEqual(run_app.home.children[0].text, "Unsupported File Type", "No unaccepted file types")
        run_app.home.ids.file_in.text = "teacup.jpg"
        run_app.home.go_btn()
        self.assertEqual(run_app.home.children[0].text, "File Not Found", "File must exist")

    def test_tool_cleanup(self):
        """
        Check that viewer window is clean after removing tools
        """
        run_app.home.ids.file_in.text = SUPPORT_FILE_PATH + "example.jpg"
        run_app.home.go_btn()
        self.assertEqual(run_app.home.file_on, True, "File loaded")

        # Run for all tools in sidebar
        og_side = copy.copy(run_app.home.ids.sidebar.children)
        og_img = copy.copy(run_app.home.display.children[0].children)
        for item in run_app.home.ids.sidebar.children:
            if isinstance(item, type(functions.RoundedButton())) and item.text != "Quit":
                # Start tool
                item.dispatch('on_press')
                item.dispatch('on_release')

                # Press again to clear
                item.dispatch('on_press')
                item.dispatch('on_release')

                self.assertListEqual(og_side, run_app.home.ids.sidebar.children, "Sidebar back to original")
                self.assertListEqual(og_img, run_app.home.display.children[0].children, "All Tools removed")

    def test_file_cleanup(self):
        og_side = copy.copy(run_app.home.ids.sidebar.children)

        # Open a file and use a tool
        run_app.home.ids.file_in.text = SUPPORT_FILE_PATH + "example.nc"
        run_app.home.go_btn()
        load_nc("Vorticity")
        self.assertEqual(len(run_app.home.ids.colorbar.children), 1, "Colorbar Added")
        select_sidebar_button("Transect Marker")
        x = run_app.home.size[0]
        y = run_app.home.size[1]

        tool = run_app.home.display.tool
        incs = np.linspace(0.4, 0.8, 10)
        x_arr = incs * x
        y_arr = incs * y
        for i in range(len(incs)):
            tool.on_touch_down(Click(float(x_arr[i]), float(y_arr[i])))

        run_app.home.ids.file_in.text = SUPPORT_FILE_PATH + "example.jpg"
        run_app.home.go_btn()

        self.assertEqual(og_side, run_app.home.ids.sidebar.children, "Sidebar restored")
        self.assertEqual(len(run_app.home.ids.colorbar.children), 0, "Colorbar removed")
        self.assertEqual(len(run_app.home.display.children), 1, "No tools on display")

    def test_project_upload(self):
        """
        Tests the project upload function of the Transect Marker tool.

        Assumes 'support/example.json' exists and is a valid project file for 'support/example.jpg' with
        a variable 'Vorticity' and three markers.
        """
        run_app.home.ids.file_in.text = SUPPORT_FILE_PATH + "example.jpg"
        run_app.home.go_btn()

        # Open Transect Marker tool
        select_sidebar_button("Transect Marker")

        # Project File
        f1 = open(SUPPORT_FILE_PATH + "example.json")
        project1 = json.load(f1)

        # Upload Project File
        multi_mark_instance = run_app.home.display.tool
        multi_mark_instance.upload_data(marker_find(project1, []))

        # Check file uploaded properly
        for i, mar in enumerate(list(project1["Vorticity"].keys())):
            p_m = project1["Vorticity"][mar]
            m_expected_points = list(zip(p_m["Click X"], p_m["Click Y"], p_m["Width"]))
            marker = multi_mark_instance.children[len(list(project1["Vorticity"].keys())) - i]
            self.assertListEqual(marker.points, m_expected_points, mar + " Points Correct")

        # Test out-of-bounds project files don't get uploaded.
        load_nc("Vorticity")

        select_sidebar_button("Transect Marker")

        # Load File
        f2 = open(SUPPORT_FILE_PATH + "test_project_file.json")
        project2 = json.load(f2)

        # Upload Project File
        multi_mark_instance = run_app.home.display.tool
        multi_mark_instance.upload_data(marker_find(project2, []))

        self.assertEqual(len(multi_mark_instance.children), 1, "Project files that don't fit in file bounds fail")
        self.assertEqual(multi_mark_instance.children[0].points, [], "Empty new marker loaded")

    def test_marker_transect(self):
        """
        Test transect marker tool management.
        """
        run_app.home.ids.file_in.text = SUPPORT_FILE_PATH + "example.jpg"
        run_app.home.go_btn()

        # Open Transect Marker tool
        sidebar = run_app.home.ids.sidebar
        select_sidebar_button("Transect Marker")

        # Project File
        f = open(SUPPORT_FILE_PATH + "example.json")
        project = json.load(f)

        # Upload Project File
        multi_mark_instance = run_app.home.display.tool
        multi_mark_instance.upload_data(marker_find(project, []))

        # Open editing mode
        select_sidebar_button("Edit Mode")

        # Delete last clicked point
        select_sidebar_button("Delete Last Point")

        # Check last clicked point was properly deleted
        m3 = project["Vorticity"]["Marker 3"]
        m3_expected_points = list(zip(m3["Click X"][:-1], m3["Click Y"][:-1], m3["Width"][:-1]))
        self.assertEqual(len(multi_mark_instance.children), 3, "Deleted fourth empty marker")
        self.assertEqual(multi_mark_instance.children[0].points, m3_expected_points, "Only the last point was deleted")

        # Delete most recent marker
        select_sidebar_button("Delete Last Line")

        # Check most recent marker was properly deleted
        self.assertEqual(len(multi_mark_instance.children), 2, "Last marker deleted")

        # Add new line
        select_sidebar_button("Back")
        select_sidebar_button("New Line")
        self.assertEqual(len(multi_mark_instance.children), 3, "New marker created")

        # Delete point
        select_sidebar_button("Edit Mode")
        select_sidebar_button("Delete Last Point")
        self.assertEqual(len(multi_mark_instance.children), 2, "Empty marker deleted")
        m2 = project["Vorticity"]["Marker 2"]
        m2_expected_points = list(zip(m2["Click X"][:-1], m2["Click Y"][:-1], m2["Width"][:-1]))
        self.assertEqual(multi_mark_instance.children[0].points, m2_expected_points, "Last point of m2 was deleted")

        # Test width adjustments
        select_sidebar_button("Back")
        select_sidebar_button("New Line")

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
        select_sidebar_button("Drag Mode")
        multi_mark_instance.on_touch_down(Click(0.43 * x, 0.43 * y))
        self.assertEqual(multi_mark_instance.children[0].points, list(zip(x_arr, y_arr, w_arr)),
                         "No new point was added")

    def test_multi_transect(self):
        """
        Test transect tool
        """
        run_app.home.ids.file_in.text = SUPPORT_FILE_PATH + "example.jpg"
        run_app.home.go_btn()
        self.assertEqual(run_app.home.file_on, True, "File loaded")

        # Open Transect Marker tool
        select_sidebar_button("Transect")

        x = run_app.home.size[0]
        y = run_app.home.size[1]
        incs = [0.5, 0.55, 0.6, 0.65]
        x_arr = incs * x
        y_arr = incs * y

        tran_instance = run_app.home.display.tool

        # First Click
        sidebar = run_app.home.ids.sidebar
        tran_instance.on_touch_down(Click(x_arr[0], y_arr[0]))
        self.assertIsNone(next((but for but in sidebar.children if but.text == "Plot"), None),
                          "No Plot Button on First Click")
        self.assertEqual(len(tran_instance.children), 1, "Transect Added")

        # Second Click
        tran_instance.on_touch_down(Click(x_arr[1], y_arr[1]))
        self.assertIsInstance(next((but for but in sidebar.children if but.text == "Plot")), Button,
                              "Plot Button added")
        self.assertEqual(len(tran_instance.children), 1, "Only one transect")

        # Third Click
        tran_instance.on_touch_down(Click(x_arr[2], y_arr[2]))
        self.assertIsNone(next((but for but in sidebar.children if but.text == "Plot"), None),
                          "Plot Button Removed")
        self.assertEqual(len(tran_instance.children), 2, "New Transect Added")

        # Repeat Click
        tran_instance.on_touch_down(Click(x_arr[2], y_arr[2]))
        self.assertIsNone(next((but for but in sidebar.children if but.text == "Plot"), None),
                          "No change when same point clicked")
        self.assertEqual(len(tran_instance.children), 2, "No change when same point clicked")

        # Drag Mode
        select_sidebar_button("Drag Mode")
        tran_instance.on_touch_down(Click(x_arr[3], y_arr[3]))
        self.assertEqual(len(tran_instance.children), 2, "No new point added when in drag mode")

        # Edit Mode: Delete Line, Delete point
        select_sidebar_button("Transect Mode")
        tran_instance.on_touch_down(Click(x_arr[3], y_arr[3]))
        select_sidebar_button("Edit Mode")
        select_sidebar_button("Delete Last Line")
        self.assertEqual(len(tran_instance.children), 1, "Only one transect now")

        select_sidebar_button("Delete Last Point")
        self.assertEqual(len(tran_instance.children), 1, "Only one transect now")
        self.assertEqual(len(tran_instance.children[0].line.points), 2, "Point deleted from transect")

        select_sidebar_button("Back")
        self.assertIsNone(next((but for but in sidebar.children if but.text == "Plot"), None),
                          "Plot Button Removed")

    def test_netcdf_config(self):
        """
        Test netcdf configuration popup ensures valid netcdf configuration settings
        """
        run_app.home.ids.file_in.text = TEST_NC_PATH
        run_app.home.go_btn()
        popup = run_app.home.nc_popup
        popup.go.dispatch('on_press')
        popup.go.dispatch('on_release')
        self.assertEqual(popup.error.text, "Please Select a Variable", "Variable must be selected")

        popup.var_select.dispatch('on_press')
        popup.var_select.dispatch('on_release')
        popup.var_drop.select("v3")
        popup.go.dispatch('on_press')
        popup.go.dispatch('on_release')
        self.assertEqual(popup.x_select.text, "i", "X dimension automatically selected")
        self.assertEqual(popup.y_select.text, "j", "Y dimension automatically selected")
        self.assertEqual(popup.z_select.text, "k", "Z dimension automatically selected")
        self.assertEqual(popup.error.text, "Please Select a Z Value", "3D variables need a Z value selected")

        popup.z_select.text = "j"
        popup.go.dispatch('on_press')
        popup.go.dispatch('on_release')
        self.assertEqual(popup.error.text, "All X, Y, Z variables must be unique", "Dimensions must be unique")

        popup.z_select.text = "Select..."
        popup.go.dispatch('on_press')
        popup.go.dispatch('on_release')
        self.assertEqual(popup.error.text, "Please Select a Z dimension", "3D variables need a Z Dimension")

        popup.z_select.text = "k"
        popup.depth_select.text = "8"
        popup.go.dispatch('on_press')
        popup.go.dispatch('on_release')
        self.assertTrue(run_app.home.file_on, "File loads when there is a proper configuration")

        run_app.home.ids.file_in.text = TEST_NC_PATH
        run_app.home.go_btn()
        popup = run_app.home.nc_popup

        popup.var_select.dispatch('on_press')
        popup.var_select.dispatch('on_release')
        popup.var_drop.select("v2")
        self.assertEqual(popup.z_select.text, "Select...", "2D Variables don't have a third dimension")

        popup.z_select.text = "j"
        popup.go.dispatch('on_press')
        popup.go.dispatch('on_release')
        self.assertEqual(popup.error.text, "All X, Y, Z variables must be unique", "Dimensions must be unique")

        popup.z_select.text = "Select..."
        popup.go.dispatch('on_press')
        popup.go.dispatch('on_release')
        self.assertTrue(run_app.home.file_on, "File loads when there is a proper configuration")

        run_app.home.ids.file_in.text = TEST_NC_PATH
        run_app.home.go_btn()
        popup = run_app.home.nc_popup
        popup.var_select.dispatch('on_press')
        popup.var_select.dispatch('on_release')
        popup.var_drop.select("v4")
        popup.depth_select.text = "70"
        popup.go.dispatch('on_press')
        popup.go.dispatch('on_release')
        self.assertEqual(popup.error.text, "This variable has more than 3 dimensions", "Can't support more than 3 dims")

        run_app.home.ids.file_in.text = TEST_NC_PATH
        run_app.home.go_btn()
        popup = run_app.home.nc_popup
        popup.var_select.dispatch('on_press')
        popup.var_select.dispatch('on_release')
        popup.var_drop.select("v1")
        popup.go.dispatch('on_press')
        popup.go.dispatch('on_release')
        self.assertEqual(popup.error.text, "This variable has less than 2 dimensions", "Can't support less than 2 dims")

    def test_setting_changes(self):
        """
        Tests implementation of setting changes. Does not test UI aspects (dropdowns) only the callback.
        """
        load_nc("Vorticity")
        display = run_app.home.display

        # Contrast updates
        og_img = copy.copy(display.img.texture)
        display.update_settings("contrast", 30)
        self.assertEqual(display.contrast, 30, "Contrast Updated")
        self.assertNotEqual(og_img, display.img.texture, "Image Updated")

        # Colormap updates
        og_img = copy.copy(display.img.texture)
        display.update_settings("colormap", "Inferno")
        self.assertEqual(display.colormap, cv2.COLORMAP_INFERNO, "Colormap Updated")
        self.assertNotEqual(og_img, display.img.texture, "Image Updated")

        # Variable
        og_img = copy.copy(display.img.texture)
        display.update_settings("variable", "Divergence")
        self.assertEqual(display.config["netcdf"]["var"], "Divergence", "Variable updated")
        self.assertNotEqual(og_img, display.img.texture, "Image Updated")

        # Circle Size
        x = run_app.home.size[0]
        y = run_app.home.size[1]
        display.update_settings("cir_size", 20)
        self.assertEqual(display.cir_size, 20, "Display circle size updated")
        select_sidebar_button("Transect")
        display.tool.on_touch_down(Click(0.43 * x, 0.43 * y))
        self.assertEqual(display.tool.children[0].c_size, (dp(20), dp(20)), "Transect graphics updated")

        select_sidebar_button("Transect Marker")
        select_sidebar_button("Transect Marker")
        display.tool.on_touch_down(Click(0.43 * x, 0.43 * y))
        self.assertEqual(display.tool.children[0].c_size, (dp(20), dp(20)), "Marker graphics updated")

        # Reset
        select_sidebar_button("Transect")

        # Line Color
        display.update_settings("l_color", "Orange")
        self.assertEqual(display.l_col, "Orange", "Display line color updated")

        select_sidebar_button("Transect")
        display.tool.on_touch_down(Click(0.43 * x, 0.43 * y))
        self.assertEqual(display.tool.children[0].l_color.rgb, [0.74, 0.42, 0.13], "Transect graphics updated")

        select_sidebar_button("Transect Marker")
        select_sidebar_button("Transect Marker")
        display.tool.on_touch_down(Click(0.43 * x, 0.43 * y))
        self.assertEqual(display.tool.children[0].l_color.rgb, [0.74, 0.42, 0.13], "Marker graphics updated")

        # Rotation
        display.rotate()
        print(type(display.rotation))
        self.assertAlmostEqual(float(display.rotation), float(45), "Rotate 45 degrees")
        display.rotate()
        self.assertAlmostEqual(float(display.rotation), float(90), "Rotated another 45 degrees")
