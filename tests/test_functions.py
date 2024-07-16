"""
Unit tests to insure transect accuracy and protect from invalid file names
"""

import unittest
from PIL import Image as Im
import numpy as np
from pathlib import Path
import json
import xarray as xr
import nccut.functions as func
from nccut.multimarker import marker_find

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
        self.assertEqual(max(app - manual), 0, "Transect on image not accurate at zero degrees")

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
        self.assertEqual(max(app - manual), 0, "Transect on image not accurate at 45 degrees")

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
        self.assertEqual(max(app - manual), 0, "Transect on image not accurate at 90 degrees")

    def test_transect_0_deg_nc(self):
        """
        Test an accurate transect is made when taken horizontally on a NetCDF file
        """
        # Setup
        dat = xr.open_dataset(SUPPORT_FILE_PATH + "example_4v.nc")['Divergence'].data
        points = [1000, 200, 1200, 200]

        # App result
        app = func.ip_get_points(points, dat, True)["Cut"]

        # Manual result
        arr = np.asarray(dat)
        rows = np.shape(arr)[0]
        manual = arr[rows - points[3] - 1:rows - points[1], points[0]:points[2]][0]
        # Compare
        self.assertEqual(max(app - manual), 0, "Transect on NetCDF not accurate at zero degrees")

    def test_transect_45_deg_nc(self):
        """
        Test an accurate transect is made when taken at 45 degrees on a NetCDF file
        """
        # Setup
        dat = xr.open_dataset(SUPPORT_FILE_PATH + "example_4v.nc")['Divergence'].data
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
        self.assertEqual(max(app - manual), 0, "Transect on NetCDF not accurate at 45 degrees")

    def test_transect_90_deg_nc(self):
        """
        Test an accurate transect is made when taken vertically on a NetCDF file
        """
        # Setup
        dat = xr.open_dataset(SUPPORT_FILE_PATH + "example_4v.nc")['Divergence'].data
        points = [1000, 100, 1000, 400]

        # App result
        app = func.ip_get_points(points, dat, True)["Cut"]

        # Manual result
        arr = np.asarray(dat)
        rows = np.shape(arr)[0]
        manual = np.ravel(np.flip(arr[rows - points[3]:rows - points[1], points[0]:points[2] + 1]))
        # Compare
        self.assertEqual(max(app - manual), 0, "Transect on NetCDF not accurate at 90 degrees")

    def test_file_names(self):
        """
        Test valid and invalid file names are correctly identified
        """
        # Setup
        rel_path = Path().absolute()

        # Test output file name rules
        self.assertFalse(func.check_file(rel_path, "", ".jpg"), "Blank file name should not be allowed")
        self.assertFalse(func.check_file(rel_path, "test$", ".json"), "No special characters should be allowed")
        self.assertFalse(func.check_file(rel_path, SUPPORT_FILE_PATH + "dir1/dir2/dir3/test", ".json"),
                         "Directories must exist")
        self.assertEqual(func.check_file(rel_path, "test.jpg", ".jpg"), "test",
                         "User entered extensions should be removed")
        self.assertEqual(func.check_file(rel_path, SUPPORT_FILE_PATH + "example", ".jpg"),
                         SUPPORT_FILE_PATH + "example(1)",
                         "If file already exists a (#) should be added")

    def test_marker_find(self):
        """
        Test whether valid project files can be accurately identified
        """
        # Data from a valid file is correctly extracted
        proper_json = open(SUPPORT_FILE_PATH + "example.json")
        proper_data = json.load(proper_json)
        marker_result = marker_find(proper_data, [])

        self.assertEqual(len(marker_result), len(proper_data["Vorticity"].keys()), "All markers weren't found")
        self.assertEqual(len(marker_result[0]), 3, "All fields weren't found")
        self.assertListEqual(marker_result[0][0], proper_data["Vorticity"]["Marker 1"]["Click X"],
                             "X Coords were not correct")
        self.assertListEqual(marker_result[1][1], proper_data["Vorticity"]["Marker 2"]["Click Y"],
                             "Y coords were not orrect")
        self.assertListEqual(marker_result[2][2], proper_data["Vorticity"]["Marker 3"]["Width"],
                             "Transect widths were not correct")

        # Output data from non marker tool fails
        multi_data = {"Multi": {"Cut 1": {"x": [1000, 2000, 3000], "y": [100, 200, 300], "Cut": [5, 10, 15]},
                                "Cut 2": {"x": [50, 60, 70, 80], "y": [20, 15, 10, 5], "Cut": [33, 66, 99]}}}
        multi_result = marker_find(multi_data, [])
        self.assertEqual(len(multi_result), 0, "Files that were outputs from Transect tool should fail")

        # All identified markers are unique
        multi_var = {"2nd Var": proper_data["Vorticity"], "Vorticity": proper_data["Vorticity"]}
        multi_var_result = marker_find(multi_var, [])
        self.assertEqual(len(multi_var_result), len(proper_data["Vorticity"].keys()), "No repeated Markers")

        # Markers without all necessary fields aren't included
        del proper_data["Vorticity"]["Marker 1"]["Click X"]
        incomplete_marker_result = marker_find(proper_data, [])

        self.assertEqual(len(incomplete_marker_result), 2, "Incomplete markers should not be included in findings")

        # A random dictionary fails
        bad_data = {"Apples": ["Fuji", "Cosmic Crisp", "Honeycrisp"]}
        bad_data_result = marker_find(bad_data, [])

        self.assertEqual(bad_data_result, [], "Random dictionaries shouldn't pass")

    def test_sel_data_2d(self):
        """
        Test whether correct netcdf data is collected from user configurations for a 2D netcdf dataset
        """
        data = xr.open_dataset(SUPPORT_FILE_PATH + "example_4v.nc")
        config1 = {"x": "x", "y": "y", "z": "Select...", "z_val": "Select...", "var": "Vorticity", "file": data}
        res1 = func.sel_data(config1)
        exp1 = np.flip(data["Vorticity"].transpose("y", "x").data, 0)
        self.assertTrue(np.array_equal(res1, exp1, equal_nan=True), "Basic settings do not match original dataset")

        config2 = {"x": "y", "y": "x", "z": "Select...", "z_val": "Select...", "var": "Divergence", "file": data}
        res2 = func.sel_data(config2)
        exp2 = np.flip(np.swapaxes(data["Divergence"].transpose("y", "x").data, 0, 1), 0)
        self.assertTrue(np.array_equal(res2, exp2, equal_nan=True),
                        "Swapped dimension settings do not match original dataset")

    def test_sel_data_3d(self):
        """
        Test whether correct netcdf data is collected from user configurations for a 3D netcdf dataset
        """
        data = xr.open_dataset(SUPPORT_FILE_PATH + "example_3d.nc")
        config1 = {"x": "i", "y": "j", "z": "k", "z_val": "15", "var": "Theta", "file": data}
        res1 = func.sel_data(config1)
        exp1 = np.flip(data["Theta"].sel(k=15).transpose("j", "i").data, 0)
        self.assertTrue(np.array_equal(res1, exp1, equal_nan=True), "Basic settings do not match original dataset")

        config2 = {"x": "j", "y": "k", "z": "i", "z_val": "3000", "var": "Theta", "file": data}
        res2 = func.sel_data(config2)
        exp2 = np.flip(data.transpose("k", "j", "i")["Theta"].sel(i=3000).data, 0)
        self.assertTrue(np.array_equal(res2, exp2, equal_nan=True),
                        "Swapped dimension settings do not match original dataset")


if __name__ == '__main__':
    unittest.main()
