"""
Unit tests to insure transect accuracy and protect from invalid file names
"""

import unittest
from PIL import Image as Im
import numpy as np
from pathlib import Path
import json
import xarray as xr
import cutview.functions as func
from cutview.multimarker import marker_find

SUPPORT_FILE_PATH = "support/"


class Test(unittest.TestCase):
    def test_transect_0_deg_img(self):
        """
        Test an accurate transect is made when taken horizontally on an image
        """
        # Setup
        img = Im.open(SUPPORT_FILE_PATH + "example.jpg").convert('RGB')
        points = [1000, 200, 1200, 200]

        # App result
        app = func.ip_get_points(points, img, False)["Cut"]

        # Manual result
        arr = np.asarray(img)
        rows = np.shape(arr)[0]
        manual = np.ravel(np.mean(arr[rows - points[3] - 1:rows - points[1], points[0]:points[2]], axis=2))
        # Compare
        self.assertEqual(max(app - manual), 0, "Transect accurate at zero degrees")

    def test_transect_45_deg_img(self):
        """
        Test an accurate transect is made when taken at 45 on an image
        """
        # Setup
        img = Im.open(SUPPORT_FILE_PATH + "example.jpg").convert('RGB')
        points = [1000, 200, 1200, 400]

        # App result
        app = func.ip_get_points(points, img, False)["Cut"]

        # Manual result
        arr = np.asarray(img)
        rows = np.shape(arr)[0]
        ix = np.arange(points[0], points[2])
        iy = np.arange(points[1], points[3])
        manual = np.ravel(np.mean(arr[rows - iy - 1, ix], axis=1))

        # Compare
        self.assertEqual(max(app - manual), 0, "Transect accurate at 45 degrees")

    def test_transect_90_deg_img(self):
        """
        Test an accurate transect is made when taken vertically on an image
        """
        # Setup
        img = Im.open(SUPPORT_FILE_PATH + "example.jpg").convert('RGB')
        points = [1000, 100, 1000, 400]

        # App result
        app = func.ip_get_points(points, img, False)["Cut"]

        # Manual result
        arr = np.asarray(img)
        rows = np.shape(arr)[0]
        manual = np.ravel(np.mean(np.flip(arr[rows - points[3]:rows - points[1], points[0]:points[2] + 1]), axis=2))

        # Compare
        self.assertEqual(max(app - manual), 0, "Transect accurate at 90 degrees")

    def test_transect_0_deg_nc(self):
        """
        Test an accurate transect is made when taken horizontally on a NetCDF file
        """
        # Setup
        dat = xr.open_dataset(SUPPORT_FILE_PATH + "example.nc")['Divergence'].data
        points = [1000, 200, 1200, 200]

        # App result
        app = func.ip_get_points(points, dat, True)["Cut"]

        # Manual result
        arr = np.asarray(dat)
        rows = np.shape(arr)[0]
        manual = arr[rows - points[3] - 1:rows - points[1], points[0]:points[2]][0]
        # Compare
        self.assertEqual(max(app - manual), 0, "Transect accurate at zero degrees")

    def test_transect_45_deg_nc(self):
        """
        Test an accurate transect is made when taken at 45 degrees on a NetCDF file
        """
        # Setup
        dat = xr.open_dataset(SUPPORT_FILE_PATH + "example.nc")['Divergence'].data
        points = [1000, 200, 1200, 400]

        # App result
        app = func.ip_get_points(points, dat, True)["Cut"]

        # Manual result
        arr = np.asarray(dat)
        rows = np.shape(arr)[0]
        ix = np.arange(points[0], points[2])
        iy = np.arange(points[1], points[3])
        manual = arr[rows - iy - 1, ix]
        # Compare
        self.assertEqual(max(app - manual), 0, "Transect accurate at 45 degrees")

    def test_transect_90_deg_nc(self):
        """
        Test an accurate transect is made when taken vertically on a NetCDF file
        """
        # Setup
        dat = xr.open_dataset(SUPPORT_FILE_PATH + "example.nc")['Divergence'].data
        points = [1000, 100, 1000, 400]

        # App result
        app = func.ip_get_points(points, dat, True)["Cut"]

        # Manual result
        arr = np.asarray(dat)
        rows = np.shape(arr)[0]
        manual = np.ravel(np.flip(arr[rows - points[3]:rows - points[1], points[0]:points[2] + 1]))
        # Compare
        self.assertEqual(max(app - manual), 0, "Transect accurate at 90 degrees")

    def test_file_names(self):
        """
        Test valid and invalid file names are correctly identified
        """
        # Setup
        rel_path = Path().absolute()

        # Test output file name rules
        self.assertFalse(func.check_file(rel_path, "", ".jpg"), "No blank file name")
        self.assertFalse(func.check_file(rel_path, "test$", ".json"), "No special characters")
        self.assertFalse(func.check_file(rel_path, SUPPORT_FILE_PATH + "dir1/dir2/dir3/test", ".json"),
                         "Directories must exist")
        self.assertEqual(func.check_file(rel_path, "test.jpg", ".jpg"), "test",
                         "Remove user entered extensions")
        self.assertEqual(func.check_file(rel_path, SUPPORT_FILE_PATH + "example", ".jpg"),
                         SUPPORT_FILE_PATH + "example(1)",
                         "If file already exists add (#)")

    def test_marker_find(self):
        """
        Test whether valid project files can be accurately identified
        """
        # Data from a valid file is correctly extracted
        proper_json = open(SUPPORT_FILE_PATH + "example.json")
        proper_data = json.load(proper_json)
        marker_result = marker_find(proper_data, [])

        self.assertEqual(len(marker_result), len(proper_data["Vorticity"].keys()), "All Markers Found")
        self.assertEqual(len(marker_result[0]), 3, "All Fields Found")
        self.assertListEqual(marker_result[0][0], proper_data["Vorticity"]["Marker 1"]["Click X"], "X Coords Correct")
        self.assertListEqual(marker_result[1][1], proper_data["Vorticity"]["Marker 2"]["Click Y"], "X Coords Correct")
        self.assertListEqual(marker_result[2][2], proper_data["Vorticity"]["Marker 3"]["Width"], "Transect Widths Correct")

        # Output data from non marker tool fails
        multi_data = {"Multi": {"Cut 1": {"x": [1000, 2000, 3000], "y": [100, 200, 300], "Cut": [5, 10, 15]},
                                "Cut 2": {"x": [50, 60, 70, 80], "y": [20, 15, 10, 5], "Cut": [33, 66, 99]}}}
        multi_result = marker_find(multi_data, [])
        self.assertEqual(len(multi_result), 0, "Files that were outputs from Transect tool fail")

        # All identified markers are unique
        multi_var = {"2nd Var": proper_data["Vorticity"], "Vorticity": proper_data["Vorticity"]}
        multi_var_result = marker_find(multi_var, [])
        self.assertEqual(len(multi_var_result), len(proper_data["Vorticity"].keys()), "No repeated Markers")

        # Markers without all necessary fields aren't included
        del proper_data["Vorticity"]["Marker 1"]["Click X"]
        incomplete_marker_result = marker_find(proper_data, [])

        self.assertEqual(len(incomplete_marker_result), 2, "Incomplete markers not included")

        # A random dictionary fails
        bad_data = {"Apples": ["Fuji", "Cosmic Crisp", "Honeycrisp"]}
        bad_data_result = marker_find(bad_data, [])

        self.assertEqual(bad_data_result, [], "Random dictionaries don't pass")

    def test_sel_data(self):
        """
        Test whether correct netcdf data is collected from user configurations
        """
        data = xr.open_dataset(SUPPORT_FILE_PATH + "example.nc")
        config1 = {"x": "x", "y": "y", "z": "Select...", "var": "Vorticity", "file": data}
        res1 = func.sel_data(config1)
        exp1 = data["Vorticity"].data
        self.assertEqual(res1.all(), exp1.all(), "Basic settings are correct")

        config2 = {"x": "y", "y": "x", "z": "Select...", "var": "Divergence", "file": data}
        res2 = func.sel_data(config2)
        exp2 = np.swapaxes(data["Divergence"].data, 0, 1)
        self.assertEqual(res2.all(), exp2.all(), "Swapped dimension settings are correct")


if __name__ == '__main__':
    unittest.main()
