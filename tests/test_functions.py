"""
Unit tests to insure transect accuracy and protect from invalid file names
"""

import unittest
from PIL import Image as Im
import numpy as np
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
        app = func.ip_get_points(points, img, {"image": SUPPORT_FILE_PATH + "example.jpg"})["Cut"]

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
        app = func.ip_get_points(points, img, {"image": SUPPORT_FILE_PATH + "example.jpg"})["Cut"]

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
        app = func.ip_get_points(points, img, {"image": SUPPORT_FILE_PATH + "example.jpg"})["Cut"]

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
        dat = xr.open_dataset(SUPPORT_FILE_PATH + "example_3d.nc")['Theta'].sel(k=0)
        config = {"netcdf": {"x": "i", "y": "j", "z": "k", "z_val": "0", "var": "Theta", "file": dat}}
        points = [100, 50, 200, 50]

        # App result
        app = func.ip_get_points(points, dat.data, config)

        # Manual result
        arr = np.asarray(dat.data)
        rows = np.shape(arr)[0]
        manual = arr[rows - points[3] - 1:rows - points[1], points[0]:points[2]][0]
        # Compare
        self.assertEqual(max(app["Cut"] - manual), 0, "Transect on NetCDF not accurate at zero degrees")
        # Check Coordinates from NetCDF
        self.assertListEqual(list(dat.coords["i"][points[0]:points[2]]), app["i"],
                             "X Coordinates for NetCDF 0 Degree Transect Incorrect")
        self.assertListEqual(np.repeat(dat.coords["j"][points[1]].data, len(manual)).tolist(), app["j"],
                             "Y Coordinates for NetCDF 0 DegreeTransect Incorrect")

    def test_transect_45_deg_nc(self):
        """
        Test an accurate transect is made when taken at 45 degrees on a NetCDF file
        """
        # Setup
        dat = xr.open_dataset(SUPPORT_FILE_PATH + "example_3d.nc")['Theta'].sel(k=0)
        config = {"netcdf": {"x": "i", "y": "j", "z": "k", "z_val": "0", "var": "Theta", "file": dat}}
        points = [100, 50, 200, 150]

        # App result
        app = func.ip_get_points(points, dat.data, config)

        # Manual result
        arr = np.asarray(dat.data)
        rows = np.shape(arr)[0]
        ix = np.arange(points[0], points[2])
        iy = np.arange(points[1], points[3])
        manual = arr[rows - iy - 1, ix]
        # Compare
        self.assertEqual(max(app["Cut"] - manual), 0, "Transect on NetCDF not accurate at 45 degrees")
        # Check Coordinates from NetCDF
        self.assertListEqual(list(dat.coords["i"][points[0]:points[2]]), app["i"],
                             "X Coordinates for NetCDF 45 Degree Transect Incorrect")
        self.assertListEqual(list(dat.coords["j"][points[1]:points[3]]), app["j"],
                             "Y Coordinates for NetCDF 45 Degree Transect Incorrect")

    def test_transect_90_deg_nc(self):
        """
        Test an accurate transect is made when taken vertically on a NetCDF file
        """
        # Setup
        dat = xr.open_dataset(SUPPORT_FILE_PATH + "example_3d.nc")['Theta'].sel(k=0)
        config = {"netcdf": {"x": "i", "y": "j", "z": "k", "z_val": "0", "var": "Theta", "file": dat}}
        points = [100, 50, 100, 150]

        # App result
        app = func.ip_get_points(points, dat.data, config)

        # Manual result
        arr = np.asarray(dat.data)
        rows = np.shape(arr)[0]
        manual = np.ravel(np.flip(arr[rows - points[3]:rows - points[1], points[0]:points[2] + 1]))
        # Compare
        self.assertEqual(max(app["Cut"] - manual), 0, "Transect on NetCDF not accurate at 90 degrees")
        # Check Coordinates from NetCDF
        self.assertListEqual(np.repeat(dat.coords["i"][points[0]].data, len(manual)).tolist(), app["i"],
                             "X Coordinates for NetCDF 90 Degree Transect Incorrect")
        self.assertListEqual(list(dat.coords["j"][points[1]:points[3]]), app["j"],
                             "Y Coordinates for NetCDF 90 Degree Transect Incorrect")

    def test_marker_find(self):
        """
        Test whether valid project files can be accurately identified
        """
        # Data from a valid file is correctly extracted
        proper_json = open(SUPPORT_FILE_PATH + "project_example.json")
        proper_data = json.load(proper_json)
        marker_result = marker_find(proper_data, [], ["Click x", "Click y", "Width"])

        self.assertEqual(len(marker_result), len(proper_data["Vorticity"].keys()), "All markers weren't found")
        self.assertEqual(len(marker_result[0]), 3, "All fields weren't found")
        self.assertListEqual(marker_result[0][0], proper_data["Vorticity"]["Marker 1"]["Click x"],
                             "X Coords were not correct")
        self.assertListEqual(marker_result[1][1], proper_data["Vorticity"]["Marker 2"]["Click y"],
                             "Y coords were not orrect")
        self.assertListEqual(marker_result[2][2], proper_data["Vorticity"]["Marker 3"]["Width"],
                             "Transect widths were not correct")

        # Output data from non marker tool fails
        multi_data = {"Multi": {"Cut 1": {"x": [1000, 2000, 3000], "y": [100, 200, 300], "Cut": [5, 10, 15]},
                                "Cut 2": {"x": [50, 60, 70, 80], "y": [20, 15, 10, 5], "Cut": [33, 66, 99]}}}
        multi_result = marker_find(multi_data, [], ["Click x", "Click y", "Width"])
        self.assertEqual(len(multi_result), 0, "Files that were outputs from Transect tool should fail")

        # All identified markers are unique
        multi_var = {"2nd Var": proper_data["Vorticity"], "Vorticity": proper_data["Vorticity"]}
        multi_var_result = marker_find(multi_var, [], ["Click x", "Click y", "Width"])
        self.assertEqual(len(multi_var_result), len(proper_data["Vorticity"].keys()), "No repeated Markers")

        # Markers without all necessary fields aren't included
        del proper_data["Vorticity"]["Marker 1"]["Click x"]
        incomplete_marker_result = marker_find(proper_data, [], ["Click x", "Click y", "Width"])

        self.assertEqual(len(incomplete_marker_result), 2, "Incomplete markers should not be included in findings")

        # A random dictionary fails
        bad_data = {"Apples": ["Fuji", "Cosmic Crisp", "Honeycrisp"]}
        bad_data_result = marker_find(bad_data, [], ["Click x", "Click y", "Width"])

        self.assertEqual(bad_data_result, [], "Random dictionaries shouldn't pass")

        # Marker coordinates must match current NetCDF file
        wrong_coords_result = marker_find(proper_data, [], ["Click Lon", "Click Lat", "Width"])
        self.assertEqual(len(wrong_coords_result), 0,
                         "Markers whose coords don't match current NetCDF file shouldn't be loaded")

    def test_sel_data_2d(self):
        """
        Test whether correct netcdf data is collected from user configurations for a 2D netcdf dataset
        """
        data = xr.open_dataset(SUPPORT_FILE_PATH + "example_4v.nc")
        config1 = {"x": "x", "y": "y", "z": "N/A", "z_val": "N/A", "var": "Vorticity", "file": data}
        res1 = func.sel_data(config1).data
        exp1 = data["Vorticity"].transpose("y", "x").data
        self.assertTrue(np.array_equal(res1, exp1, equal_nan=True), "Basic settings do not match original dataset")

        config2 = {"x": "y", "y": "x", "z": "N/A", "z_val": "N/A", "var": "Divergence", "file": data}
        res2 = func.sel_data(config2).data
        exp2 = np.swapaxes(data["Divergence"].transpose("y", "x").data, 0, 1)
        self.assertTrue(np.array_equal(res2, exp2, equal_nan=True),
                        "Swapped dimension settings do not match original dataset")

    def test_sel_data_3d(self):
        """
        Test whether correct netcdf data is collected from user configurations for a 3D netcdf dataset
        """
        data = xr.open_dataset(SUPPORT_FILE_PATH + "example_3d.nc")
        config1 = {"x": "i", "y": "j", "z": "k", "z_val": "15", "var": "Theta", "file": data}
        res1 = func.sel_data(config1).data
        exp1 = data["Theta"].sel(k=15).transpose("j", "i").data
        self.assertTrue(np.array_equal(res1, exp1, equal_nan=True), "Basic settings do not match original dataset")

        config2 = {"x": "j", "y": "k", "z": "i", "z_val": "3000", "var": "Theta", "file": data}
        res2 = func.sel_data(config2)
        exp2 = data.transpose("k", "j", "i")["Theta"].sel(i=3000).data
        self.assertTrue(np.array_equal(res2, exp2, equal_nan=True),
                        "Swapped dimension settings do not match original dataset")

    def test_subset_around_transect(self):
        """
        Test subset properly includes a margin only when it is possible and click points are properly rescaled
        """
        # NetCDF
        nc = xr.open_dataset(SUPPORT_FILE_PATH + "example_4v.nc")
        img = np.asarray(Im.open(SUPPORT_FILE_PATH + "example.jpg"))
        config = {"x": "x", "y": "y", "z": "N/A", "z_val": "N/A", "var": "Vorticity", "file": nc}
        data_arr = [("NC", func.sel_data(config)), ("image", img)]

        for d in data_arr:
            # Middle
            data = d[1]
            mid_clicks = [500, 500, 600, 600]
            mid_expected_points = [3, 3, 103, 103]
            mid_expected_scales = [497, 497]
            mid_result_data, mid_result_points, mid_result_scales = func.subset_around_transect(data, mid_clicks)

            if d[0] == "NC":
                m_e_data = data[497: 604, 497: 604].data
                m_r_data = mid_result_data.data
            else:
                m_e_data = np.flip(data, 0)[497: 604, 497: 604]  # Origin lower left
                m_r_data = np.flip(mid_result_data, 0)  # Origin upper right
            self.assertTrue(np.array_equal(m_r_data, m_e_data, equal_nan=True),
                            "Subset of " + d[0] + " in center did not include a proper margin")
            self.assertTrue(np.array_equal(mid_result_points, mid_expected_points, equal_nan=True),
                            "Points were not properly rescaled to the central subset of the " + d[0] + " data")
            self.assertTrue(np.array_equal(mid_result_scales, mid_expected_scales, equal_nan=True),
                            "Point scale factors were incorrect for the central subset of the " + d[0] + " data")
            # 1 Edge
            edge_clicks = [1, 500, 101, 600]
            edge_expected_points = [0, 3, 100, 103]
            edge_expected_scales = [497, 1]
            edge_result_data, edge_result_points, edge_result_scales = func.subset_around_transect(data, edge_clicks)

            if d[0] == "NC":
                e_e_data = data[497: 604, 1: 105].data
                e_r_data = edge_result_data.data
            else:
                e_e_data = np.flip(data, 0)[497: 604, 1: 105]  # Origin lower left
                e_r_data = np.flip(edge_result_data, 0)  # Origin upper right
            self.assertTrue(np.array_equal(e_e_data, e_r_data, equal_nan=True),
                            "Subset of " + d[0] + " data on one edge did not include a proper margin")
            self.assertTrue(np.array_equal(edge_result_points, edge_expected_points, equal_nan=True),
                            "Points were not properly rescaled to the subset of the " + d[0] + " data on one edge")
            self.assertTrue(np.array_equal(edge_result_scales, edge_expected_scales, equal_nan=True),
                            "Point scale factors were incorrect for the subset of the " + d[0] + " data on one edge")

            # 2 Edges
            end = data.shape[1]
            two_edge_clicks = [end - 100, 1, end, 101]
            two_edge_expected_points = [3, 0, 103, 100]
            two_edge_expected_scales = [1, end - 103]
            two_edge_res_data, two_edge_res_points, two_edge_res_scales = func.subset_around_transect(data,
                                                                                                      two_edge_clicks)
            if d[0] == "NC":
                t_e_e_data = data[1: 105, end - 103: end].data
                t_e_r_data = two_edge_res_data.data
            else:
                t_e_e_data = np.flip(data, 0)[1: 105, end - 103: end]  # Origin lower left
                t_e_r_data = np.flip(two_edge_res_data, 0)  # Origin upper right
            self.assertTrue(np.array_equal(t_e_e_data, t_e_r_data, equal_nan=True),
                            "Subset of " + d[0] + " data on two edges did not include a proper margin")
            self.assertTrue(np.array_equal(two_edge_res_points, two_edge_expected_points, equal_nan=True),
                            "Points were not properly rescaled to the subset of the " + d[0] + " data on two edges")
            self.assertTrue(np.array_equal(two_edge_res_scales, two_edge_expected_scales, equal_nan=True),
                            "Point scale factors were incorrect for the subset of the " + d[0] + " data on two edges")


if __name__ == '__main__':
    unittest.main()
