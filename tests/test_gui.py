# SPDX-FileCopyrightText: 2024 University of Washington
#
# SPDX-License-Identifier: BSD-3-Clause

"""
Unit tests for GUI functionality
"""

import unittest
import os
import time
import copy
import pooch
import json
import tempfile
import numpy as np
import xarray as xr
from functools import partial
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from nccut.orthogonalchainwidth import OrthogonalChainWidth
import nccut.functions as functions
from nccut.nccut import NcCut

os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'
TEST_NC_PATH = pooch.retrieve(url="doi:10.5281/zenodo.12734574/test_nc.nc", known_hash=None)
EXAMPLE_JPG_PATH = pooch.retrieve(url="doi:10.5281/zenodo.14525966/example.jpg",
                                  known_hash="f039e8cb72d6821f4909707767863373230159e384a26ba7edd8a01a3e359e53")
EXAMPLE_3D_PATH = pooch.retrieve(url="doi:10.5281/zenodo.14525966/example_3d.nc",
                                 known_hash="ccb6c76062d3228799746e68e1bb3ff715538bc3aae796c577c6fb1d06fcdc9f")
EXAMPLE_4V_PATH = pooch.retrieve(url="doi:10.5281/zenodo.14525966/example_4v.nc",
                                 known_hash="afd261063f4b58c382c46db0d81e69dfb8f5234ef0037b261087177e6d3f7e1b")
ORTHOGONAL_CHAIN_DATA_EXAMPLE_PATH = pooch.retrieve(url="doi:10.5281/zenodo.14525966/orthogonal_project_example.json",
                                                    known_hash='82f37306b94ee54ad1906c6bed72f8c9e8243940f95a8fe1f0d39a27eb920091')
INLINE_CHAIN_DATA_EXAMPLE_PATH = pooch.retrieve(url="doi:10.5281/zenodo.14525966/inline_project_example.json",
                                                known_hash='9f0f1d4d536cc445ccfc5aa07a011a32379673a114fbe2b7be7070bd2f73e9b5')


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
    run_app.home.ids.file_in.text = EXAMPLE_4V_PATH
    run_app.home.load_btn()
    popup = run_app.home.nc_popup
    popup.var_select.text = variable
    popup.x_select.text = "x"
    popup.y_select.text = "y"
    popup.load.dispatch("on_press")
    popup.load.dispatch("on_release")


def load_3d_nc(z_val):
    run_app.home.ids.file_in.text = EXAMPLE_3D_PATH
    run_app.home.load_btn()
    popup = run_app.home.nc_popup
    popup.var_select.text = "Theta"
    popup.x_select.text = "i"
    popup.y_select.text = "j"
    popup.z_select.text = "k"
    popup.depth_select.text = z_val
    popup.load.dispatch("on_press")
    popup.load.dispatch("on_release")


def select_sidebar_button(text):
    sidebar = run_app.home.ids.dynamic_sidebar
    but = next((but for but in sidebar.children if isinstance(but, Button) and but.text == text), None)
    if but:
        but.dispatch('on_press')
        but.dispatch('on_release')
    else:
        raise Exception("Button not in Sidebar")


class Test(unittest.TestCase):
    # Test cases
    @classmethod
    def setUpClass(cls):
        get_app()

    def test_file_names(self):
        """
        Test input file name rules
        """
        run_app.home.ids.file_in.text = " *$%&@! "
        run_app.home.load_btn()
        self.assertEqual(run_app.home.children[0].text, "Invalid File Name",
                         "File names with irregular characters are invalid")
        self.assertEqual(run_app.home.ids.file_in.text, "*$%&@!", "Whitespace not removed from file entry")
        run_app.home.ids.file_in.text = ""
        run_app.home.load_btn()
        self.assertEqual(run_app.home.children[0].text, "Invalid File Name", "Empty file names are invalid")
        run_app.home.ids.file_in.text = ORTHOGONAL_CHAIN_DATA_EXAMPLE_PATH
        run_app.home.load_btn()
        self.assertEqual(run_app.home.children[0].text, "Unsupported File Type", "No unaccepted file types")
        run_app.home.ids.file_in.text = "teacup.jpg"
        run_app.home.load_btn()
        self.assertEqual(run_app.home.children[0].text, "File Not Found", "File must exist")

    def test_tool_cleanup(self):
        """
        Check that viewer window is clean after removing tools
        """
        run_app.home.ids.file_in.text = EXAMPLE_JPG_PATH
        run_app.home.load_btn()
        self.assertEqual(run_app.home.file_on, True, "File was not loaded")

        # Run for all tools in sidebar
        og_side = ["Orthogonal Chain", "Inline Chain"]
        og_img = copy.copy(run_app.home.display.children[0].children)
        sidebar = run_app.home.ids.dynamic_sidebar.children
        for item in sidebar:
            if isinstance(item, type(functions.RoundedButton())):
                # Start tool
                item.dispatch('on_press')
                item.dispatch('on_release')

                # Close Tool
                run_app.home.display.close_tool_btn.dispatch('on_press')
                run_app.home.display.close_tool_btn.dispatch('on_release')

                self.assertListEqual(og_side,
                                     [b.text for b in sidebar if isinstance(b, type(functions.RoundedButton()))],
                                     "Sidebar did not revert to original")
                self.assertListEqual(og_img, run_app.home.display.children[0].children, "All Tools were not removed")

    def test_file_cleanup(self):
        """
        Tests all tools, file elements, and sidebar additions are reset when a new file is opened.
        """
        # Open a file and use a tool
        run_app.home.ids.file_in.text = EXAMPLE_4V_PATH
        run_app.home.load_btn()
        load_2d_nc("Vorticity")
        og_side = ["Orthogonal Chain", "Inline Chain"]

        self.assertEqual(len(run_app.home.color_bar_box.children), 1, "Colorbar was not Added")
        self.assertIsNotNone(run_app.home.color_bar_box.parent, "Colorbar box was not displayed")
        self.assertIsNotNone(run_app.home.netcdf_info.parent, "NetCDF Info bar was not displayed")
        self.assertIsNotNone(run_app.home.settings_bar.parent, "Settings bar was not displayed")
        self.assertIsNotNone(run_app.home.settings_bar.netcdf_btn.parent, "NetCDF settings button was not displayed")
        select_sidebar_button("Orthogonal Chain")
        x = run_app.home.size[0]
        y = run_app.home.size[1]

        tool = run_app.home.display.tool
        incs = np.linspace(0.4, 0.8, 10)
        x_arr = incs * x
        y_arr = incs * y
        for i in range(len(incs)):
            tool.on_touch_down(functions.Click(float(x_arr[i]), float(y_arr[i])))

        run_app.home.ids.file_in.text = EXAMPLE_JPG_PATH
        run_app.home.load_btn()
        sidebar = run_app.home.ids.dynamic_sidebar.children
        self.assertListEqual(og_side,
                             [b.text for b in sidebar if isinstance(b, type(functions.RoundedButton()))],
                             "Sidebar did not revert to original")
        self.assertEqual(len(run_app.home.color_bar_box.children), 0, "Colorbar was not removed")
        self.assertIsNone(run_app.home.color_bar_box.parent, "Colorbar box was not removed")
        self.assertIsNone(run_app.home.netcdf_info.parent, "NetCDF info bar was not removed")
        self.assertIsNone(run_app.home.netcdf_info.parent, "NetCDF info bar was not removed")
        self.assertIsNone(run_app.home.settings_bar.netcdf_btn.parent, "NetCDF settings menu was not removed")
        self.assertEqual(len(run_app.home.display.children), 1, "Not all tools were removed from display")

    def test_data_load(self):
        """
        Tests the chain data load function of the tools.

        Assumes chain data files are valid for 'support/example_4v.nc' with
        a variable 'Vorticity' and three chains.
        """
        load_2d_nc("Vorticity")

        # Open Orthogonal Chain tool
        select_sidebar_button("Orthogonal Chain")

        # Chain Data File
        f1 = open(ORTHOGONAL_CHAIN_DATA_EXAMPLE_PATH)
        cdata1 = json.load(f1)
        # Load Chain Data File
        multi_chain_instance = run_app.home.display.tool
        multi_chain_instance.load_data(functions.chain_find(cdata1, [], ["Click x", "Click y", "Width"], "Orthogonal"))

        # Check file loaded properly
        for i, chain in enumerate(list(cdata1["Vorticity"].keys())[:-1]):
            p_c = cdata1["Vorticity"][chain]
            c_expected_points = list(zip(p_c["Click x"], p_c["Click y"], p_c["Width"]))
            o_chain = multi_chain_instance.children[len(list(cdata1["Vorticity"].keys())) - 1 - i]
            self.assertListEqual(o_chain.points, c_expected_points,
                                 chain + " Orthogonal Chain Points Did not Load Properly")

        self.assertEqual(multi_chain_instance.children[0].points, [],
                         "Empty new orthogonal chain was created after load")
        select_sidebar_button("Close Tool")
        # Open Inline Chain tool
        select_sidebar_button("Inline Chain")

        # Chain Data File
        f2 = open(INLINE_CHAIN_DATA_EXAMPLE_PATH)
        cdata1 = json.load(f2)
        # Load Chain Data File
        multi_chain_instance = run_app.home.display.tool
        multi_chain_instance.load_data(functions.chain_find(cdata1, [], ["Click x", "Click y"], "Inline"))

        # Check file loaded properly
        for i, chain in enumerate(list(cdata1["Vorticity"].keys())[:-1]):
            p_c = cdata1["Vorticity"][chain]
            c_expected_points = list(zip(p_c["Click x"], p_c["Click y"]))
            i_chain = multi_chain_instance.children[len(list(cdata1["Vorticity"].keys())) - 1 - i]
            self.assertListEqual(i_chain.points, c_expected_points,
                                 chain + " Inline Chain Points Did not Load Properly")

        self.assertEqual(multi_chain_instance.children[0].points, [],
                         "Empty new inline chain was created after load")

    def test_orthogonal_chain(self):
        """
        Test that orthogonal chain tool exhibits expected behavior.
        """
        run_app.home.ids.file_in.text = EXAMPLE_JPG_PATH
        run_app.home.load_btn()

        load_2d_nc("Vorticity")

        # Open Orthogonal Chain tool
        sidebar = run_app.home.ids.dynamic_sidebar.children
        select_sidebar_button("Orthogonal Chain")

        # Chain Data File
        f = open(ORTHOGONAL_CHAIN_DATA_EXAMPLE_PATH)
        cdata = json.load(f)

        # Load Chain Data File
        multi_chain_instance = run_app.home.display.tool
        multi_chain_instance.load_data(functions.chain_find(cdata, [], ["Click x", "Click y", "Width"], "Orthogonal"))

        # Test Chain Exporting
        with tempfile.TemporaryDirectory() as jpath:
            multi_chain_instance.save_data(os.path.join(jpath, "test.json"))
            f = open(os.path.join(jpath, "test.json"))
            res1 = json.load(f)
            f.close()
            self.assertEqual(list(res1.keys())[0], "Vorticity", "NetCDF Variable not found")
            self.assertEqual(list(res1.keys())[1], "global_metadata", "Global metadata not found")
            self.assertEqual(len(list(res1["Vorticity"].keys())), 4, "Not all chains found")
            self.assertEqual(len(list(res1["Vorticity"]["Orthogonal Chain 1"].keys())), 14,
                             "Not all transects and group data found")

        # Open editing mode
        select_sidebar_button("Edit Mode")

        # Delete last clicked point
        select_sidebar_button("Delete Last Point")

        # Check last clicked point was properly deleted
        c3 = cdata["Vorticity"]["Orthogonal Chain 3"]
        c3_expected_points = list(zip(c3["Click x"][:-1], c3["Click y"][:-1], c3["Width"][:-1]))
        self.assertEqual(len(multi_chain_instance.children), 3, "Empty fourth chain was not deleted")
        self.assertEqual(multi_chain_instance.children[0].points, c3_expected_points, "Expected points were not found")

        # Delete most recent chain
        select_sidebar_button("Delete Last Chain")

        # Check most recent chain was properly deleted
        self.assertEqual(len(multi_chain_instance.children), 2, "Last chain was not deleted properly")

        # Add new chain
        select_sidebar_button("Back")
        select_sidebar_button("New Chain")
        self.assertEqual(len(multi_chain_instance.children), 3, "New chain was not created")

        # Delete point
        select_sidebar_button("Edit Mode")
        select_sidebar_button("Delete Last Point")
        self.assertEqual(len(multi_chain_instance.children), 2, "Empty chain was not deleted")
        c2 = cdata["Vorticity"]["Orthogonal Chain 2"]
        c2_expected_points = list(zip(c2["Click x"][:-1], c2["Click y"][:-1], c2["Width"][:-1]))
        self.assertEqual(multi_chain_instance.children[0].points, c2_expected_points,
                         "Last point of c2 was not deleted")

        # Delete until only one point
        while len(multi_chain_instance.children) != 1 and multi_chain_instance.children[0].points != 1:
            select_sidebar_button("Delete Last Point")

        select_sidebar_button("Back")
        self.assertNotIn(multi_chain_instance.width_btn, sidebar,
                         "Width adjustment button in sidebar when only one point clicked")
        select_sidebar_button("Edit Mode")
        select_sidebar_button("Delete Last Point")
        select_sidebar_button("Back")
        self.assertNotIn(multi_chain_instance.p_btn, sidebar,
                         "Plot button not removed from sidebar when no more chains left")

        # Simulate chain clicks with width changes
        x = run_app.home.size[0]
        y = run_app.home.size[1]

        incs = np.linspace(0.4, 0.8, 10)
        x_arr = (incs * x).tolist()
        y_arr = (incs * y).tolist()
        w_arr = [int(n * 100) for n in incs]
        w_arr[0] = 44
        multi_chain_instance.on_touch_down(functions.Click(float(x_arr[0]), float(y_arr[0])))
        for i in range(1, len(incs)):
            w_wid = OrthogonalChainWidth(multi_chain_instance)
            w_wid.txt.text = str(w_arr[i])
            w_wid.set_btn.dispatch('on_press')
            w_wid.set_btn.dispatch('on_release')
            multi_chain_instance.on_touch_down(functions.Click(float(x_arr[i]), float(y_arr[i])))
        self.assertEqual(multi_chain_instance.children[0].points, list(zip(x_arr, y_arr, w_arr)),
                         "Points were not selected with appropriate width adjustments")

        # Test Drag Mode
        select_sidebar_button("Drag Mode")
        multi_chain_instance.on_touch_down(functions.Click(0.43 * x, 0.43 * y))
        self.assertEqual(multi_chain_instance.children[0].points, list(zip(x_arr, y_arr, w_arr)),
                         "A point was added while tool in drag mode")

    def test_inline_chain(self):
        """
        Test inline chain tool exhibits expected behavior
        """
        run_app.home.ids.file_in.text = EXAMPLE_JPG_PATH
        run_app.home.load_btn()
        self.assertEqual(run_app.home.file_on, True, "File was not loaded")

        # Open Inline Chain tool
        select_sidebar_button("Inline Chain")

        x = run_app.home.size[0]
        y = run_app.home.size[1]
        incs = np.array([0.4, 0.45, 0.55])
        x_arr = incs * x
        y_arr = incs * y

        tran_instance = run_app.home.display.tool
        # First Click
        sidebar = run_app.home.ids.dynamic_sidebar.children
        tran_instance.on_touch_down(functions.Click(float(x_arr[0]), float(y_arr[0])))
        self.assertNotIn(tran_instance.p_btn, sidebar, "There cannot be a Plot Button on First Click")
        self.assertEqual(len(tran_instance.children), 1, "Inline chain Not Added")

        # Second Click
        tran_instance.on_touch_down(functions.Click(float(x_arr[1]), float(y_arr[1])))
        self.assertIn(tran_instance.p_btn, sidebar, "Plot Button should be added on second click")
        self.assertEqual(len(tran_instance.children), 1, "A chain was improperly deleted or added")

        # Third Click
        tran_instance.on_touch_down(functions.Click(float(x_arr[2]), float(y_arr[2])))
        self.assertIn(tran_instance.p_btn, sidebar, "Plot Button should be there on third click")
        self.assertEqual(len(tran_instance.children), 1, "A chain was improperly deleted or added")

        self.assertEqual(tran_instance.children[0].points, list(zip(x_arr, y_arr)),
                         "Chain points were not placed correctly")

        # Test Chain Exporting
        with tempfile.TemporaryDirectory() as jpath:
            tran_instance.save_data(os.path.join(jpath, "test.json"))
            f = open(os.path.join(jpath, "test.json"))
            res1 = json.load(f)
            f.close()
            self.assertEqual(list(res1.keys())[0], "Inline Chain 1", "Chain not found")
            self.assertEqual(list(res1.keys())[1], "global_metadata", "Global metadata not found")
            self.assertEqual(len(list(res1["Inline Chain 1"].keys())), 4,
                             "Not all transects and group data found")

        # Repeat Click
        tran_instance.on_touch_down(functions.Click(float(x_arr[2]), float(y_arr[2])))
        self.assertEqual(tran_instance.children[0].points, list(zip(x_arr, y_arr)),
                         "Point was added where there was already a point")

        # Test Drag Mode
        select_sidebar_button("Drag Mode")
        tran_instance.on_touch_down(functions.Click(0.43 * x, 0.43 * y))
        self.assertEqual(tran_instance.children[0].points, list(zip(x_arr, y_arr)),
                         "A point was added while tool in drag mode")

        # Create new chain
        select_sidebar_button("Transect Mode")
        select_sidebar_button("New Chain")
        self.assertEqual(len(tran_instance.children), 2, "Inline Chain Not Added")
        select_sidebar_button("New Chain")
        self.assertEqual(len(tran_instance.children), 2,
                         "New chain was added even though previous chain had no clicks")
        tran_instance.on_touch_down(functions.Click(0.43 * x, 0.43 * y))
        self.assertEqual(tran_instance.children[1].points, list(zip(x_arr, y_arr)),
                         "A point was added to previous chain")
        self.assertEqual(tran_instance.children[0].points, [(0.43 * x, 0.43 * y)],
                         "Point was not added to new chain")

        # Edit mode
        select_sidebar_button("Edit Mode")
        select_sidebar_button("Delete Last Point")
        self.assertEqual(tran_instance.children[0].points, [], "Chain point was not properly deleted")
        select_sidebar_button("Delete Last Point")
        self.assertEqual(len(tran_instance.children), 1,
                         "Empty chain was not deleted when last point was deleted")
        self.assertEqual(tran_instance.children[0].points, list(zip(x_arr, y_arr))[:-1],
                         "Chain point was not deleted from previous chain after current chain was removed")
        select_sidebar_button("Delete Last Chain")
        self.assertEqual(len(tran_instance.children), 1, "When last chain is deleted, a new chain is added")
        self.assertNotIn(tran_instance.p_btn, sidebar)
        self.assertEqual(tran_instance.children[0].points, [], "Chain was not properly deleted")

    def test_netcdf_config(self):
        """
        Test netcdf configuration popup ensures valid netcdf configuration settings
        """
        run_app.home.general_config = {"graphics_defaults": {"contrast": 0, "line_color": "Blue", "colormap": "viridis",
                                                             "circle_size": 5},
                                       "netcdf": {"dimension_order": ["z", "y", "x"]},
                                       "tool_defaults": {"orthogonal_width": 40},
                                       "metadata": {}}
        run_app.home.ids.file_in.text = TEST_NC_PATH
        run_app.home.load_btn()
        popup = run_app.home.nc_popup

        # Check Default Values and rejection of a 1D Variable
        self.assertEqual(popup.var_select.text, "v1", "First variable was not automatically selected on start up")
        self.assertEqual(popup.x_select.text, "i", "X dimension not selected correctly")
        self.assertEqual(popup.y_select.text, "N/A", "Y dimension detected for 1D variable")
        self.assertEqual(popup.z_select.text, "N/A", "Z dimension detected for 1D variable")
        self.assertEqual(popup.z_select.text, "N/A", "Z dimension value chosen for 1D variable")

        popup.load.dispatch('on_press')
        popup.load.dispatch('on_release')
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
        popup.load.dispatch('on_press')
        popup.load.dispatch('on_release')
        self.assertEqual(popup.error.text, "All X, Y, Z variables must be unique", "Dimensions must be unique")

        popup.y_select.text = "j"
        popup.load.dispatch('on_press')
        popup.load.dispatch('on_release')
        self.assertTrue(run_app.home.file_on, "File did not load when there was a proper configuration")

        # Check 3D Variable behavior
        run_app.home.ids.file_in.text = TEST_NC_PATH
        run_app.home.load_btn()
        popup = run_app.home.nc_popup
        popup.var_select.dispatch('on_press')
        popup.var_select.dispatch('on_release')
        popup.var_drop.select("v3")

        self.assertEqual(popup.x_select.text, "i", "X dimension not selected correctly")
        self.assertEqual(popup.y_select.text, "j", "Y dimension not selected correctly")
        self.assertEqual(popup.z_select.text, "k", "Z dimension not selected correctly")
        self.assertEqual(popup.depth_select.text, "0", "First Z dimension value not chosen for 3D variable")

        popup.z_select.text = "j"
        popup.load.dispatch('on_press')
        popup.load.dispatch('on_release')
        self.assertEqual(popup.error.text, "All X, Y, Z variables must be unique", "Dimensions must be unique")

        popup.z_select.text = "k"
        popup.load.dispatch('on_press')
        popup.load.dispatch('on_release')
        self.assertTrue(run_app.home.file_on, "File did not load when there was a proper configuration")

        # Check Rejection of a 4D Variable
        run_app.home.ids.file_in.text = TEST_NC_PATH
        run_app.home.load_btn()
        popup = run_app.home.nc_popup
        popup.var_select.dispatch('on_press')
        popup.var_select.dispatch('on_release')
        popup.var_drop.select("v4")
        popup.load.dispatch('on_press')
        popup.load.dispatch('on_release')
        self.assertEqual(popup.error.text, "This variable has more than 3 dimensions", "Can't support more than 3 dims")

    def test_netcdf_settings(self):
        """
        Tests implementation of netcdf setting changes. Does not test UI aspects (dropdowns) only the callback.
        """
        load_2d_nc("Vorticity")
        display = run_app.home.display

        # Contrast updates
        og_img = copy.copy(display.img.texture)
        display.update_settings("contrast", 10)
        self.assertEqual(display.contrast, 2.0, "Contrast increase was not updated properly on contrast change")
        display.update_settings("contrast", -10)
        self.assertEqual(display.contrast, 0.5, "Contrast increase was not updated properly on contrast change")
        self.assertNotEqual(og_img, display.img.texture, "Image was not updated on contrast change")

        # Colormap updates
        og_img = copy.copy(display.img.texture)
        display.update_settings("colormap", "inferno")
        self.assertEqual(display.colormap, "inferno", "Colormap was not updated on colormap change")
        self.assertNotEqual(og_img, display.img.texture, "Image was not updated on colormap change")

        # Variable
        og_img = copy.copy(display.img.texture)
        display.update_settings("variable", "Divergence")
        self.assertEqual(display.config["netcdf"]["var"], "Divergence", "Variable was not updated on variable change")
        self.assertNotEqual(og_img, display.img.texture, "Image was not updated on variable change")

        # Z Value
        load_3d_nc("-0.5")
        display = run_app.home.display
        og_img = copy.copy(display.img.texture)
        display.update_settings("depth", "-7.595")
        self.assertEqual(display.config["netcdf"]["z_val"], "-7.595", "Z Value was not updated on z value change")
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
        select_sidebar_button("Inline Chain")
        display.tool.on_touch_down(functions.Click(0.43 * x, 0.43 * y))
        self.assertEqual(display.tool.children[0].c_size, (dp(20), dp(20)),
                         "Inline chain graphics did not update on circle size change")

        select_sidebar_button("Close Tool")
        select_sidebar_button("Orthogonal Chain")
        display.tool.on_touch_down(functions.Click(0.43 * x, 0.43 * y))
        self.assertEqual(display.tool.children[0].c_size, (dp(20), dp(20)),
                         "Orthogonal chain graphics were not updated on circle size change")

        # Reset
        select_sidebar_button("Close Tool")

        # Line Color
        display.update_settings("l_color", "Orange")
        self.assertEqual(display.l_col, "Orange", "Display line color was not updated on line color setting change")

        select_sidebar_button("Inline Chain")
        display.tool.on_touch_down(functions.Click(0.43 * x, 0.43 * y))
        self.assertEqual(display.tool.children[0].l_color.rgb, [0.74, 0.42, 0.13],
                         "Inline chain graphics were not updated on line color setting change")

        select_sidebar_button("Close Tool")
        select_sidebar_button("Orthogonal Chain")
        display.tool.on_touch_down(functions.Click(0.43 * x, 0.43 * y))
        self.assertEqual(display.tool.children[0].l_color.rgb, [0.74, 0.42, 0.13],
                         "Orthogonal chain graphics were not updated on line color size change")

    def test_load_nonuniform_coords(self):
        """
        Test that when loading a DataArray when nonuniform coordinates the resulting image is interpolated to the
        coordinate data
        """
        run_app.home.ids.file_in.text = EXAMPLE_3D_PATH
        run_app.home.load_btn()
        popup = run_app.home.nc_popup
        popup.var_select.text = "Theta"
        popup.x_select.text = "i"
        popup.y_select.text = "k"
        popup.z_select.text = "j"
        popup.depth_select.text = "2780"
        popup.load.dispatch("on_press")
        popup.load.dispatch("on_release")

        netcdf_dat = xr.open_dataset(EXAMPLE_3D_PATH)
        x_coord = netcdf_dat["i"].data
        y_coord = netcdf_dat["k"].data

        x_pix = min(abs(x_coord[:-1] - x_coord[1:]))
        y_pix = min(abs(y_coord[:-1] - y_coord[1:]))
        x = np.arange(x_coord.min(), x_coord.max() + x_pix, x_pix)
        y = np.arange(y_coord.min(), y_coord.max() + y_pix, y_pix)
        expected_size = [x.shape[0], y.shape[0]]
        self.assertEqual(run_app.home.display.size, expected_size, "Loaded data with nonuniform coordinates does not "
                                                                   "match expected size.")

    def test_plot_popup_2d_nc(self):
        """
        Test the plotting and data saving functionality of the plotting popup. Infers some knowledge of popup structure
        to test variable and transect selection process. Mainly the callbacks for selecting checkboxes and saving
        data/plots checkboxes.
        """
        # Loading 4 Variable NetCDF file
        load_2d_nc("Vorticity")

        # Draw 2 orthogonal chains
        x = run_app.home.size[0]
        y = run_app.home.size[1]
        c1_incs = np.array([0.5, 0.55, 0.6, 0.65])
        c1_x_arr = c1_incs * x
        c1_y_arr = c1_incs * y

        c2_incs = np.array([0.3, 0.35, 0.4, 0.45])
        c2_x_arr = c2_incs * x
        c2_y_arr = c2_incs * y
        select_sidebar_button("Orthogonal Chain")
        tool = run_app.home.display.tool
        for i in range(len(c1_incs)):
            tool.on_touch_down(functions.Click(float(c1_x_arr[i]), float(c1_y_arr[i])))
        select_sidebar_button("New Chain")
        for i in range(len(c2_incs)):
            tool.on_touch_down(functions.Click(float(c2_x_arr[i]), float(c2_y_arr[i])))
        select_sidebar_button("Plot Data")
        plot_popup = run_app.home.plot_popup

        # Initial Transect Selections
        with tempfile.TemporaryDirectory() as jpath:
            plot_popup.download_selected_data(os.path.join(jpath, "test.json"))
            f = open(os.path.join(jpath, "test.json"))
            res1 = json.load(f)
            f.close()
            self.assertListEqual(list(res1["Vorticity"].keys()), ["Orthogonal Chain 1", "Vorticity_attrs"],
                                 "Only selected chain and metadata should be saved")
            self.assertIn("global_metadata", list(res1.keys()), "Global metadata not added")
            self.assertEqual(len(list(res1["Vorticity"]["Orthogonal Chain 1"].keys())), 6,
                             "Orthogonal Chain should have 3 transects and Click x, Click y, Width")
        # Plot Saving
        with tempfile.TemporaryDirectory() as ipath:
            plot_popup.download_png_plot(os.path.join(ipath, "test"))
            self.assertTrue(os.path.isfile(os.path.join(ipath, "test.png")), "PNG Plot not saved")

        with tempfile.TemporaryDirectory() as ppath:
            plot_popup.download_pdf_plot(os.path.join(ppath, "test"))
            self.assertTrue(os.path.isfile(os.path.join(ppath, "test.pdf")), "PDF Plot not saved")

        # Can't deselect all transects
        dummy_check = CheckBox(active=False)
        plot_popup.on_transect_checkbox(dummy_check, "Orthogonal Chain 1", "Cut 3")
        self.assertFalse(dummy_check.active, "More options still available")
        plot_popup.on_transect_checkbox(dummy_check, "Orthogonal Chain 1", "Cut 2")
        self.assertFalse(dummy_check.active, "More options still available")
        plot_popup.on_transect_checkbox(dummy_check, "Orthogonal Chain 1", "Cut 1")
        self.assertTrue(dummy_check.active, "User should not be able to deselect all transects")

        # Selecting Specific Transects
        plot_popup.on_transect_checkbox(dummy_check, "Orthogonal Chain 2", "Cut 2")
        with tempfile.TemporaryDirectory() as jpath:
            plot_popup.download_selected_data(os.path.join(jpath, "test.json"))
            f = open(os.path.join(jpath, "test.json"))
            res2 = json.load(f)
            f.close()
            self.assertListEqual(list(res2["Vorticity"].keys()),
                                 ["Orthogonal Chain 1", "Orthogonal Chain 2", "Vorticity_attrs"],
                                 "Two chains were selected so two should be saved")
            self.assertIn("global_metadata", list(res2.keys()), "Global metadata not added")
            self.assertEqual(len(list(res2["Vorticity"]["Orthogonal Chain 1"].keys())), 4,
                             "Orthogonal Chan 1 should have 1 transect and Click x, Click y, Width")
            self.assertEqual(list(res2["Vorticity"]["Orthogonal Chain 1"].keys())[0], "Cut 1",
                             "Orthogonal Chain 1 should only have Cut 1 transect")
            self.assertEqual(len(list(res2["Vorticity"]["Orthogonal Chain 2"].keys())), 4,
                             "Orthogonal Chain 2 should have 1 transect and Click x, Click y, Width")
            self.assertEqual(list(res2["Vorticity"]["Orthogonal Chain 2"].keys())[0], "Cut 2",
                             "Orthogonal Chain 2 should only have Cut 2 transect")
        # Selecting multiple variables
        dummy_check = CheckBox(active=False)
        plot_popup.on_var_checkbox(dummy_check, "Vorticity")
        self.assertTrue(dummy_check.active, "User should not be able to deselect all variables")
        plot_popup.on_var_checkbox(dummy_check, "Divergence")
        with tempfile.TemporaryDirectory() as jpath:
            plot_popup.download_selected_data(os.path.join(jpath, "test.json"))
            f = open(os.path.join(jpath, "test.json"))
            res3 = json.load(f)
            f.close()
            self.assertListEqual(list(res3.keys()), ["Vorticity", "Divergence", "global_metadata"],
                                 "Two variables were selected but two weren't saved")
            self.assertIn("Vorticity_attrs", list(res3["Vorticity"].keys()), "Vorticity metadata was not saved")
            self.assertIn("Divergence_attrs", list(res3["Divergence"].keys()), "Divergence metadata was not saved")
        plot_popup.dismiss()

    def test_plot_popup_3d_nc(self):
        """
        Test the plotting and data saving functionality of the plotting popup. Infers some knowledge of popup structure
        to test selection process. Mainly the callbacks for selecting z value checkboxes and saving data/plots.
        """
        # Loading 3D NetCDF File
        load_3d_nc("-0.5")

        # Draw 2 chains
        x = run_app.home.size[0]
        y = run_app.home.size[1]
        incs = np.array([0.4, 0.45, 0.5, 0.55, 0.6, 0.65])
        x_arr = incs * x
        y_arr = incs * y
        select_sidebar_button("Inline Chain")
        tool = run_app.home.display.tool
        for i in range(3):
            tool.on_touch_down(functions.Click(float(x_arr[i]), float(y_arr[i])))
        select_sidebar_button("New Chain")
        for i in range(3, 6):
            tool.on_touch_down(functions.Click(float(x_arr[i]), float(y_arr[i])))
        select_sidebar_button("Plot Data")
        self.assertEqual(len(tool.children), 2, "2 Chains Not Added")
        plot_popup = run_app.home.plot_popup

        # Selecting multiple z values
        dummy_check = CheckBox(active=False)
        plot_popup.on_z_checkbox(dummy_check, "-0.5")
        self.assertTrue(dummy_check.active, "User should not be able to deselect all z values")
        plot_popup.on_z_checkbox(dummy_check, "-7.595")
        plot_popup.on_z_checkbox(dummy_check, "-21.125")
        with tempfile.TemporaryDirectory() as jpath:
            plot_popup.download_selected_data(os.path.join(jpath, "test.json"))
            f = open(os.path.join(jpath, "test.json"))
            res1 = json.load(f)
            f.close()
            self.assertEqual(list(res1["Theta"].keys()), ["-0.5", "-7.595", "-21.125", "Theta_attrs"],
                             "Three z values were selected so three should have been saved")
        # Saving all z data
        with tempfile.TemporaryDirectory() as jpath:
            plot_popup.download_all_z_data(os.path.join(jpath, "test.json"))
            f = open(os.path.join(jpath, "test.json"))
            res2 = json.load(f)
            f.close()
            self.assertEqual(len(list(res2["Theta"].keys())), 19, "All z values should have been saved")

        # Ensure one chain requirement for the all z plot
        dummy_check = CheckBox(active=False)
        plot_popup.on_inline_chain_checkbox(dummy_check, "Inline Chain 2")
        og_plot = str(plot_popup.plot)
        plot_popup.get_all_z_plot()
        self.assertEqual(og_plot, str(plot_popup.plot),
                         "If more than one chain is selected all Z values should not be plotted")
        dummy_check = CheckBox(active=False)
        plot_popup.on_inline_chain_checkbox(dummy_check, "Inline Chain 1")
        plot_popup.get_all_z_plot()
        self.assertNotEqual(og_plot, str(plot_popup.plot),
                            "If only one chain is selected the all z plot should be created")

    def test_metadata_and_config_file(self):
        """
        Tests whether a passed valid configuration dictionary is properly used to change settings in the app.
        """
        non_default_config = {"graphics_defaults": {"contrast": 6, "line_color": "Green", "colormap": "plasma",
                                                    "circle_size": 50},
                              "netcdf": {"dimension_order": ["z", "x", "y"]},
                              "tool_defaults": {"orthogonal_width": 20},
                              "metadata": {"new_field": "new_val"}}
        run_app.home.general_config = non_default_config
        run_app.home.ids.file_in.text = EXAMPLE_3D_PATH
        run_app.home.load_btn()
        popup = run_app.home.nc_popup
        self.assertEqual(popup.x_select.text, "j", "Dimension order was not updated from config file.")
        self.assertEqual(popup.y_select.text, "i", "Dimension order was not updated from config file.")
        self.assertEqual(popup.z_select.text, "k", "Dimension order was not updated from config file.")
        self.assertEqual(popup.depth_select.text, "-0.5", "Dimension order was not updated from config file.")
        popup.load.dispatch("on_press")
        popup.load.dispatch("on_release")

        self.assertEqual(run_app.home.display.colormap, non_default_config["graphics_defaults"]["colormap"],
                         "Colormap was not updated from config file.")
        self.assertEqual(run_app.home.display.contrast,
                         functions.contrast_function(non_default_config["graphics_defaults"]["contrast"]),
                         "Contrast was not updated from config file.")

        x = run_app.home.size[0]
        y = run_app.home.size[1]
        c1_incs = np.array([0.5, 0.55, 0.6, 0.65])
        c1_x_arr = c1_incs * x
        c1_y_arr = c1_incs * y
        select_sidebar_button("Orthogonal Chain")
        tool = run_app.home.display.tool
        for i in range(len(c1_incs)):
            tool.on_touch_down(functions.Click(float(c1_x_arr[i]), float(c1_y_arr[i])))
        self.assertEqual(run_app.home.display.l_col, non_default_config["graphics_defaults"]["line_color"],
                         "Tool line color was not updated from config file.")
        c = non_default_config["graphics_defaults"]["circle_size"]
        self.assertEqual(tool.children[0].c_size, (dp(c), dp(c)),
                         "Tool graphics size was not updated from config file.")
        self.assertEqual(tool.curr_width, 20, "Default orthogonal chain width was not updated from config file.")
        select_sidebar_button("Plot Data")
        plot_popup = run_app.home.plot_popup
        with tempfile.TemporaryDirectory() as jpath:
            plot_popup.download_selected_data(os.path.join(jpath, "test.json"))
            f = open(os.path.join(jpath, "test.json"))
            res = json.load(f)
            f.close()
            self.assertIn("global_metadata", list(res.keys()))
            self.assertListEqual(list(res["global_metadata"].keys()),
                                 ["time_stamp", "user", "license", "new_field", "file", "netcdf_attrs", "dim_attrs"],
                                 "Some or all global attributes including ones from config weren't included in output")
            self.assertListEqual(list(res["global_metadata"]["dim_attrs"].keys()), ["j", "i", "k"],
                                 "Dimension attributes for each dimension weren't collected.")
            self.assertListEqual(list(res["global_metadata"]["dim_attrs"]["j"].keys()),
                                 ["standard_name", "axis", "long_name", "swap_dim"],
                                 "Dimension attributes for each dimension weren't collected.")
            self.assertIn("Theta_attrs", list(res["Theta"].keys()),
                          "Variable specific attributes weren't included in output")
            self.assertListEqual(list(res["Theta"]["Theta_attrs"].keys()), ["standard_name", "long_name", "units"],
                                 "Some or all variable specific attributes missing from output.")
