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
from kivy.uix.checkbox import CheckBox

import sys
sys.path.insert(0, 'src/nccut')  # Test local code not PyPI

from nccut.multimarker import Click, marker_find
from nccut.markerwidth import MarkerWidth
import nccut.functions as functions
from nccut.nccut import NcCut

os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'
SUPPORT_FILE_PATH = "support/"
TEST_NC_PATH = pooch.retrieve(url="doi:10.5281/zenodo.12734574/test_nc.nc", known_hash=None)


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
    app = NcCut()
    p = partial(run_tests, app)
    Clock.schedule_once(p, 0.000001)
    app.run()


def load_2d_nc(variable):
    run_app.home.ids.file_in.text = SUPPORT_FILE_PATH + "example_4v.nc"
    run_app.home.go_btn()
    popup = run_app.home.nc_popup
    popup.var_select.text = variable
    popup.x_select.text = "x"
    popup.y_select.text = "y"
    popup.go.dispatch("on_press")
    popup.go.dispatch("on_release")


def load_3d_nc(z_val):
    run_app.home.ids.file_in.text = SUPPORT_FILE_PATH + "example_3d.nc"
    run_app.home.go_btn()
    popup = run_app.home.nc_popup
    popup.var_select.text = "Theta"
    popup.x_select.text = "i"
    popup.y_select.text = "j"
    popup.z_select.text = "k"
    popup.depth_select.text = z_val
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
        self.assertEqual(run_app.home.children[0].text, "Invalid File Name",
                         "File names with irregular characters are invalid")
        run_app.home.ids.file_in.text = ""
        run_app.home.go_btn()
        self.assertEqual(run_app.home.children[0].text, "Invalid File Name", "Empty file names are invalid")
        run_app.home.ids.file_in.text = SUPPORT_FILE_PATH + "project_example.json"
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
        self.assertEqual(run_app.home.file_on, True, "File was not loaded")

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

                self.assertListEqual(og_side, run_app.home.ids.sidebar.children, "Sidebar did not revert to original")
                self.assertListEqual(og_img, run_app.home.display.children[0].children, "All Tools were not removed")

    def test_file_cleanup(self):
        og_side = copy.copy(run_app.home.ids.sidebar.children)

        # Open a file and use a tool
        run_app.home.ids.file_in.text = SUPPORT_FILE_PATH + "example_4v.nc"
        run_app.home.go_btn()
        load_2d_nc("Vorticity")
        self.assertEqual(len(run_app.home.ids.colorbar.children), 1, "Colorbar was not Added")
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

        self.assertEqual(og_side, run_app.home.ids.sidebar.children, "Sidebar was not restored")
        self.assertEqual(len(run_app.home.ids.colorbar.children), 0, "Colorbar was not removed")
        self.assertEqual(len(run_app.home.display.children), 1, "Not all tools were removed from display")

    def test_project_upload(self):
        """
        Tests the project upload function of the Transect Marker tool.

        Assumes 'support/project_example.json' exists and is a valid project file for 'support/example.jpg' with
        a variable 'Vorticity' and three markers.
        """
        load_2d_nc("Vorticity")

        # Open Transect Marker tool
        select_sidebar_button("Transect Marker")

        # Project File
        f1 = open(SUPPORT_FILE_PATH + "project_example.json")
        project1 = json.load(f1)
        # Upload Project File
        multi_mark_instance = run_app.home.display.tool
        multi_mark_instance.upload_data(marker_find(project1, [], ["Click x", "Click y", "Width"]))

        # Check file uploaded properly
        for i, mar in enumerate(list(project1["Vorticity"].keys())):
            p_m = project1["Vorticity"][mar]
            m_expected_points = list(zip(p_m["Click x"], p_m["Click y"], p_m["Width"]))
            marker = multi_mark_instance.children[len(list(project1["Vorticity"].keys())) - i]
            self.assertListEqual(marker.points, m_expected_points, mar + " Marker Points Did not Upload Properly")

        self.assertEqual(multi_mark_instance.children[0].points, [], "Empty new marker was created after upload")

    def test_marker_transect(self):
        """
        Test transect marker tool management.
        """
        run_app.home.ids.file_in.text = SUPPORT_FILE_PATH + "example.jpg"
        run_app.home.go_btn()

        load_2d_nc("Vorticity")

        # Open Transect Marker tool
        sidebar = run_app.home.ids.sidebar
        select_sidebar_button("Transect Marker")

        # Project File
        f = open(SUPPORT_FILE_PATH + "project_example.json")
        project = json.load(f)

        # Upload Project File
        multi_mark_instance = run_app.home.display.tool
        multi_mark_instance.upload_data(marker_find(project, [], ["Click x", "Click y", "Width"]))

        # Open editing mode
        select_sidebar_button("Edit Mode")

        # Delete last clicked point
        select_sidebar_button("Delete Last Point")

        # Check last clicked point was properly deleted
        m3 = project["Vorticity"]["Marker 3"]
        m3_expected_points = list(zip(m3["Click x"][:-1], m3["Click y"][:-1], m3["Width"][:-1]))
        self.assertEqual(len(multi_mark_instance.children), 3, "Empty fourth marker was not deleted")
        self.assertEqual(multi_mark_instance.children[0].points, m3_expected_points, "Expected points were not found")

        # Delete most recent marker
        select_sidebar_button("Delete Last Line")

        # Check most recent marker was properly deleted
        self.assertEqual(len(multi_mark_instance.children), 2, "Last marker was not deleted properly")

        # Add new line
        select_sidebar_button("Back")
        select_sidebar_button("New Line")
        self.assertEqual(len(multi_mark_instance.children), 3, "New marker was not created")

        # Delete point
        select_sidebar_button("Edit Mode")
        select_sidebar_button("Delete Last Point")
        self.assertEqual(len(multi_mark_instance.children), 2, "Empty marker was not deleted")
        m2 = project["Vorticity"]["Marker 2"]
        m2_expected_points = list(zip(m2["Click x"][:-1], m2["Click y"][:-1], m2["Width"][:-1]))
        self.assertEqual(multi_mark_instance.children[0].points, m2_expected_points, "Last point of m2 was not deleted")

        # Test width adjustments
        select_sidebar_button("Back")
        select_sidebar_button("New Line")

        # Simulate marker press with width changes
        x = run_app.home.size[0]
        y = run_app.home.size[1]

        incs = np.linspace(0.4, 0.8, 10)
        x_arr = (incs * x).tolist()
        y_arr = (incs * y).tolist()
        w_arr = [int(n * 100) for n in incs]
        w_arr[0] = 44
        multi_mark_instance.on_touch_down(Click(float(x_arr[0]), float(y_arr[0])))
        w_wid = next((but for but in sidebar.children if isinstance(but, MarkerWidth)), None)
        for i in range(1, len(incs)):
            w_wid.txt.text = str(w_arr[i])
            w_wid.btn.dispatch('on_press')
            w_wid.btn.dispatch('on_release')
            multi_mark_instance.on_touch_down(Click(float(x_arr[i]), float(y_arr[i])))
        self.assertEqual(multi_mark_instance.children[0].points, list(zip(x_arr, y_arr, w_arr)),
                         "Points were not selected with appropriate width adjustments")

        # Test Drag Mode
        select_sidebar_button("Drag Mode")
        multi_mark_instance.on_touch_down(Click(0.43 * x, 0.43 * y))
        self.assertEqual(multi_mark_instance.children[0].points, list(zip(x_arr, y_arr, w_arr)),
                         "A point was added while tool in drag mode")

    def test_multi_transect(self):
        """
        Test transect tool
        """
        run_app.home.ids.file_in.text = SUPPORT_FILE_PATH + "example.jpg"
        run_app.home.go_btn()
        self.assertEqual(run_app.home.file_on, True, "File was not loaded")

        # Open Transect Marker tool
        select_sidebar_button("Transect")

        x = run_app.home.size[0]
        y = run_app.home.size[1]
        incs = np.array([0.4, 0.45, 0.55, 0.6])
        x_arr = incs * x
        y_arr = incs * y

        tran_instance = run_app.home.display.tool
        # First Click
        sidebar = run_app.home.ids.sidebar
        tran_instance.on_touch_down(Click(float(x_arr[0]), float(y_arr[0])))
        self.assertIsNone(next((but for but in sidebar.children if but.text == "Plot"), None),
                          "There cannot be a Plot Button on First Click")
        self.assertEqual(len(tran_instance.children), 1, "Transect Not Added")

        # Second Click
        tran_instance.on_touch_down(Click(float(x_arr[1]), float(y_arr[1])))
        self.assertIsInstance(next((but for but in sidebar.children if but.text == "Plot")), Button,
                              "Plot Button should be added on second click")
        self.assertEqual(len(tran_instance.children), 1, "A transect was improperly deleted or added")

        # Third Click
        tran_instance.on_touch_down(Click(float(x_arr[2]), float(y_arr[2])))
        self.assertIsNone(next((but for but in sidebar.children if but.text == "Plot"), None),
                          "Plot Button should be Removed when a new incomplete transect is drawn")
        self.assertEqual(len(tran_instance.children), 2, "New Transect was not Added")

        # Repeat Click
        tran_instance.on_touch_down(Click(float(x_arr[2]), float(y_arr[2])))
        self.assertIsNone(next((but for but in sidebar.children if but.text == "Plot"), None),
                          "Nothing should happen when same point is clicked")
        self.assertEqual(len(tran_instance.children), 2, "Nothing should happen when same point is clicked")

        # Drag Mode
        select_sidebar_button("Drag Mode")
        tran_instance.on_touch_down(Click(float(x_arr[3]), float(y_arr[3])))
        self.assertEqual(len(tran_instance.children), 2, "A new point was added when tool was in drag mode")

        # Edit Mode: Delete Line, Delete point
        select_sidebar_button("Transect Mode")
        tran_instance.on_touch_down(Click(float(x_arr[3]), float(y_arr[3])))
        select_sidebar_button("Edit Mode")
        select_sidebar_button("Delete Last Line")
        self.assertEqual(len(tran_instance.children), 1, "Transect did not delete properly")

        select_sidebar_button("Delete Last Point")
        self.assertEqual(len(tran_instance.children), 1, "Transect added or delete unexpectedly")
        self.assertEqual(len(tran_instance.children[0].line.points), 2, "Point was not deleted from transect")

        select_sidebar_button("Back")
        self.assertIsNone(next((but for but in sidebar.children if but.text == "Plot"), None),
                          "Plot Button was not Removed when number of points became odd through deleteion")

    def test_netcdf_config(self):
        """
        Test netcdf configuration popup ensures valid netcdf configuration settings
        """
        run_app.home.ids.file_in.text = TEST_NC_PATH
        run_app.home.go_btn()
        popup = run_app.home.nc_popup

        # Check Default Values and rejection of a 1D Variable
        self.assertEqual(popup.var_select.text, "v1", "First variable was not automatically selected on start up")
        self.assertEqual(popup.x_select.text, "i", "X dimension not selected correctly")
        self.assertEqual(popup.y_select.text, "N/A", "Y dimension detected for 1D variable")
        self.assertEqual(popup.z_select.text, "N/A", "Z dimension detected for 1D variable")
        self.assertEqual(popup.z_select.text, "N/A", "Z dimension value chosen for 1D variable")

        popup.go.dispatch('on_press')
        popup.go.dispatch('on_release')
        self.assertEqual(popup.error.text, "This variable has less than 2 dimensions", "Can't support less than 2 dims")

        # Check 2D Variable behavior
        popup.var_select.dispatch('on_press')
        popup.var_select.dispatch('on_release')
        popup.var_drop.select("v2")

        self.assertEqual(popup.x_select.text, "i", "X dimension not selected correctly")
        self.assertEqual(popup.y_select.text, "j", "Y dimension not selected correctly")
        self.assertEqual(popup.z_select.text, "N/A", "Third dimension detected for a 2D variable")
        self.assertEqual(popup.z_select.text, "N/A", "Z dimension value chosen for 2D variable")

        popup.y_select.text = "i"
        popup.go.dispatch('on_press')
        popup.go.dispatch('on_release')
        self.assertEqual(popup.error.text, "All X, Y, Z variables must be unique", "Dimensions must be unique")

        popup.y_select.text = "j"
        popup.go.dispatch('on_press')
        popup.go.dispatch('on_release')
        self.assertTrue(run_app.home.file_on, "File did not load when there was a proper configuration")

        # Check 3D Variable behavior
        run_app.home.ids.file_in.text = TEST_NC_PATH
        run_app.home.go_btn()
        popup = run_app.home.nc_popup
        popup.var_select.dispatch('on_press')
        popup.var_select.dispatch('on_release')
        popup.var_drop.select("v3")

        self.assertEqual(popup.x_select.text, "i", "X dimension not selected correctly")
        self.assertEqual(popup.y_select.text, "j", "Y dimension not selected correctly")
        self.assertEqual(popup.z_select.text, "k", "Z dimension not selected correctly")
        self.assertEqual(popup.depth_select.text, "0", "First Z dimension value not chosen for 3D variable")

        popup.z_select.text = "j"
        popup.go.dispatch('on_press')
        popup.go.dispatch('on_release')
        self.assertEqual(popup.error.text, "All X, Y, Z variables must be unique", "Dimensions must be unique")

        popup.z_select.text = "k"
        popup.go.dispatch('on_press')
        popup.go.dispatch('on_release')
        self.assertTrue(run_app.home.file_on, "File did not load when there was a proper configuration")

        # Check Rejection of a 4D Variable
        run_app.home.ids.file_in.text = TEST_NC_PATH
        run_app.home.go_btn()
        popup = run_app.home.nc_popup
        popup.var_select.dispatch('on_press')
        popup.var_select.dispatch('on_release')
        popup.var_drop.select("v4")
        popup.go.dispatch('on_press')
        popup.go.dispatch('on_release')
        self.assertEqual(popup.error.text, "This variable has more than 3 dimensions", "Can't support more than 3 dims")

    def test_netcdf_settings(self):
        """
        Tests implementation of netcdf setting changes. Does not test UI aspects (dropdowns) only the callback.
        """
        load_2d_nc("Vorticity")
        display = run_app.home.display

        # Contrast updates
        og_img = copy.copy(display.img.texture)
        display.update_settings("contrast", 30)
        self.assertEqual(display.contrast, 30, "Contrast was not updated on contrast change")
        self.assertNotEqual(og_img, display.img.texture, "Image was not updated on contrast change")

        # Colormap updates
        og_img = copy.copy(display.img.texture)
        display.update_settings("colormap", "Inferno")
        self.assertEqual(display.colormap, cv2.COLORMAP_INFERNO, "Colormap was not updated on colormap change")
        self.assertNotEqual(og_img, display.img.texture, "Image was not updated on colormap change")

        # Variable
        og_img = copy.copy(display.img.texture)
        display.update_settings("variable", "Divergence")
        self.assertEqual(display.config["netcdf"]["var"], "Divergence", "Variable was not updated on variable change")
        self.assertNotEqual(og_img, display.img.texture, "Image was not updated on variable change")

        # Z Value
        load_3d_nc("15")
        display = run_app.home.display
        og_img = copy.copy(display.img.texture)
        display.update_settings("depth", "30")
        self.assertEqual(display.config["netcdf"]["z_val"], "30", "Z Value was not updated on z value change")
        self.assertNotEqual(og_img, display.img.texture, "Image was not updated on z value change")

    def test_view_settings(self):
        """
        Tests implementation of viewer setting changes. Does not test UI aspects (dropdowns) only the callback.
        """
        load_2d_nc("Vorticity")
        display = run_app.home.display
        # Circle Size
        x = run_app.home.size[0]
        y = run_app.home.size[1]
        display.update_settings("cir_size", 20)
        self.assertEqual(display.cir_size, 20, "Display circle size was not updated on setting change")
        select_sidebar_button("Transect")
        display.tool.on_touch_down(Click(0.43 * x, 0.43 * y))
        self.assertEqual(display.tool.children[0].c_size, (dp(20), dp(20)),
                         "Transect graphics did not update on circle size change")

        select_sidebar_button("Transect Marker")
        select_sidebar_button("Transect Marker")
        display.tool.on_touch_down(Click(0.43 * x, 0.43 * y))
        self.assertEqual(display.tool.children[0].c_size, (dp(20), dp(20)),
                         "Marker graphics were not updated on circle size change")

        # Reset
        select_sidebar_button("Transect")

        # Line Color
        display.update_settings("l_color", "Orange")
        self.assertEqual(display.l_col, "Orange", "Display line color was not updated on line color setting change")

        select_sidebar_button("Transect")
        display.tool.on_touch_down(Click(0.43 * x, 0.43 * y))
        self.assertEqual(display.tool.children[0].l_color.rgb, [0.74, 0.42, 0.13],
                         "Transect graphics were not updated on line color setting change")

        select_sidebar_button("Transect Marker")
        select_sidebar_button("Transect Marker")
        display.tool.on_touch_down(Click(0.43 * x, 0.43 * y))
        self.assertEqual(display.tool.children[0].l_color.rgb, [0.74, 0.42, 0.13],
                         "Marker graphics were not updated on line color size change")

        # Rotation
        display.rotate()
        self.assertEqual(np.round(display.rotation, 4), float(45), "Display did not rotate 45 degrees")
        display.rotate()
        self.assertEqual(np.round(display.rotation, 4), float(90), "Display only rotated 45 degrees once")

    def test_plot_popup_2d_nc(self):
        """
        Test the plotting and data saving functionality of the plotting popup. Infers some knowledge of popup structure
        to test variable and transect selection process. Mainly the callbacks for selecting checkboxes and saving
        data/plots checkboxes.
        """
        # Loading 4 Variable NetCDF file
        load_2d_nc("Vorticity")

        # Draw 2 Markers
        x = run_app.home.size[0]
        y = run_app.home.size[1]
        m1_incs = np.array([0.5, 0.55, 0.6, 0.65])
        m1_x_arr = m1_incs * x
        m1_y_arr = m1_incs * y

        m2_incs = np.array([0.3, 0.35, 0.4, 0.45])
        m2_x_arr = m2_incs * x
        m2_y_arr = m2_incs * y
        select_sidebar_button("Transect Marker")
        tool = run_app.home.display.tool
        for i in range(len(m1_incs)):
            tool.on_touch_down(Click(float(m1_x_arr[i]), float(m1_y_arr[i])))
        select_sidebar_button("New Line")
        for i in range(len(m2_incs)):
            tool.on_touch_down(Click(float(m2_x_arr[i]), float(m2_y_arr[i])))
        select_sidebar_button("Plot")
        plot_popup = tool.plotting

        # Initial Transect Selections
        plot_popup.download_selected_data("__test__")
        f = open("__test__.json")
        res1 = json.load(f)
        f.close()
        os.remove("__test__.json")
        self.assertEqual(len(list(res1["Vorticity"].keys())), 1, "Only selected marker should be saved")
        self.assertEqual(len(list(res1["Vorticity"]["Marker 1"].keys())), 6,
                         "Marker should have 3 transects and Click x, Click y, Width")

        # Plot Saving
        plot_popup.download_png_plot("__test__")
        self.assertTrue(os.path.isfile("__test__.png"), "PNG Plot not saved")
        os.remove("__test__.png")

        plot_popup.download_pdf_plot("__test__")
        self.assertTrue(os.path.isfile("__test__.pdf"), "PDF Plot not saved")
        os.remove("__test__.pdf")

        # Can't deselect all transects
        dummy_check = CheckBox(active=False)
        plot_popup.on_transect_checkbox(dummy_check, "Marker 1", "Cut 3")
        self.assertFalse(dummy_check.active, "More options still available")
        plot_popup.on_transect_checkbox(dummy_check, "Marker 1", "Cut 2")
        self.assertFalse(dummy_check.active, "More options still available")
        plot_popup.on_transect_checkbox(dummy_check, "Marker 1", "Cut 1")
        self.assertTrue(dummy_check.active, "User should not be able to deselect all transects")

        # Selecting Specific Transects
        plot_popup.on_transect_checkbox(dummy_check, "Marker 2", "Cut 2")
        plot_popup.download_selected_data("__test__")
        f = open("__test__.json")
        res2 = json.load(f)
        f.close()
        os.remove("__test__.json")
        self.assertEqual(len(list(res2["Vorticity"].keys())), 2, "Two markers were selected so two should be saved")
        self.assertEqual(len(list(res2["Vorticity"]["Marker 1"].keys())), 4,
                         "Marker 1 should have 1 transect and Click x, Click y, Width")
        self.assertEqual(list(res2["Vorticity"]["Marker 1"].keys())[0], "Cut 1",
                         "Marker 1 should only have Cut 1 transect")
        self.assertEqual(len(list(res2["Vorticity"]["Marker 2"].keys())), 4,
                         "Marker 2 should have 1 transect and Click x, Click y, Width")
        self.assertEqual(list(res2["Vorticity"]["Marker 2"].keys())[0], "Cut 2",
                         "Marker 2 should only have Cut 2 transect")

        # Selecting multiple variables
        dummy_check = CheckBox(active=False)
        plot_popup.on_var_checkbox(dummy_check, "Vorticity")
        self.assertTrue(dummy_check.active, "User should not be able to deselect all variables")
        plot_popup.on_var_checkbox(dummy_check, "Divergence")
        plot_popup.download_selected_data("__test__")
        f = open("__test__.json")
        res3 = json.load(f)
        f.close()
        os.remove("__test__.json")
        self.assertEqual(len(list(res3.keys())), 2, "Two variables were selected but two weren't saved")
        plot_popup.dismiss()

    def test_plot_popup_3d_nc(self):
        """
        Test the plotting and data saving functionality of the plotting popup. Infers some knowledge of popup structure
        to test selection process. Mainly the callbacks for selecting z value checkboxes and saving data/plots.
        """
        # Loading 3D NetCDF File
        load_3d_nc("15")

        # Draw 2 Single Transects
        x = run_app.home.size[0]
        y = run_app.home.size[1]
        incs = np.array([0.5, 0.55, 0.6, 0.65])
        x_arr = incs * x
        y_arr = incs * y
        select_sidebar_button("Transect")
        tool = run_app.home.display.tool
        for i in range(len(incs)):
            tool.on_touch_down(Click(float(x_arr[i]), float(y_arr[i])))
        select_sidebar_button("Plot")
        plot_popup = tool.plotting

        # Selecting multiple z values
        dummy_check = CheckBox(active=False)
        plot_popup.on_z_checkbox(dummy_check, "15")
        self.assertTrue(dummy_check.active, "User should not be able to deselect all z values")
        plot_popup.on_z_checkbox(dummy_check, "30")
        plot_popup.on_z_checkbox(dummy_check, "60")
        plot_popup.download_selected_data("__test__")
        f = open("__test__.json")
        res1 = json.load(f)
        f.close()
        os.remove("__test__.json")
        self.assertEqual(list(res1["Theta"].keys()), ["15", "30", "60"],
                         "Three z values were selected so three should have been saved")

        # Saving all z data
        plot_popup.download_all_z_data("__test__")
        f = open("__test__.json")
        res2 = json.load(f)
        f.close()
        os.remove("__test__.json")
        self.assertEqual(len(list(res2["Theta"].keys())), 18, "All z values should have been saved")

        # Ensure one transect requirement for the all z plot
        og_plot = str(plot_popup.plot)
        plot_popup.get_all_z_plot()
        self.assertEqual(og_plot, str(plot_popup.plot),
                         "If more than one transect is selected all Z values should not be plotted")
        dummy_check = CheckBox(active=False)
        plot_popup.on_transect_checkbox(dummy_check, "Multi", "Cut 2")
        plot_popup.get_all_z_plot()
        self.assertNotEqual(og_plot, str(plot_popup.plot),
                            "If only one transect is selected the all z plot should be created")
