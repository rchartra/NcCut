# SPDX-FileCopyrightText: 2024 University of Washington
#
# SPDX-License-Identifier: BSD-3-Clause

"""
Unit tests to insure transect accuracy and protect from invalid file names
"""

import unittest
from PIL import Image as Im
import numpy as np
import json
import pooch
import xarray as xr
import nccut.functions as func
from nccut.multiorthogonalchain import orthogonal_chain_find

EXAMPLE_JPG_PATH = pooch.retrieve(url="doi:10.5281/zenodo.14512874/example.jpg",
                                  known_hash="f039e8cb72d6821f4909707767863373230159e384a26ba7edd8a01a3e359e53")
EXAMPLE_3D_PATH = pooch.retrieve(url="doi:10.5281/zenodo.14512874/example_3d.nc",
                                 known_hash="ccb6c76062d3228799746e68e1bb3ff715538bc3aae796c577c6fb1d06fcdc9f")
EXAMPLE_4V_PATH = pooch.retrieve(url="doi:10.5281/zenodo.14512874/example_4v.nc",
                                 known_hash="afd261063f4b58c382c46db0d81e69dfb8f5234ef0037b261087177e6d3f7e1b")
PROJECT_EXAMPLE_PATH = pooch.retrieve(url="doi:10.5281/zenodo.14512874/project_example.json",
                                      known_hash='82f37306b94ee54ad1906c6bed72f8c9e8243940f95a8fe1f0d39a27eb920091')


class Test(unittest.TestCase):
    def test_transect_0_deg_img(self):
        """
        Test an accurate transect is made when taken horizontally on an image
        """
        # Setup
        img = Im.open(EXAMPLE_JPG_PATH).convert('RGB')
        points = [1000, 200, 1200, 200]

        # App result
        app = func.ip_get_points(points, img, {"image": EXAMPLE_JPG_PATH})["Cut"]

        # Manual result
        arr = np.asarray(img)
        manual = np.ravel(np.mean(arr[points[1]:points[3] + 1, points[0]:points[2]], axis=2))
        # Compare
        self.assertEqual(max(app - manual), 0, "Transect on image not accurate at zero degrees")

    def test_transect_45_deg_img(self):
        """
        Test an accurate transect is made when taken at 45 on an image
        """
        # Setup
        img = Im.open(EXAMPLE_JPG_PATH).convert('RGB')
        points = [1000, 200, 1200, 400]

        # App result
        app = func.ip_get_points(points, img, {"image": EXAMPLE_JPG_PATH})["Cut"]

        # Manual result
        arr = np.asarray(img)
        ix = np.arange(points[0], points[2])
        iy = np.arange(points[1], points[3])
        manual = np.ravel(np.mean(arr[iy, ix], axis=1))

        # Compare
        self.assertEqual(max(app - manual), 0, "Transect on image not accurate at 45 degrees")

    def test_transect_90_deg_img(self):
        """
        Test an accurate transect is made when taken vertically on an image
        """
        # Setup
        img = Im.open(EXAMPLE_JPG_PATH).convert('RGB')
        points = [1000, 100, 1000, 400]

        # App result
        app = func.ip_get_points(points, img, {"image": EXAMPLE_JPG_PATH})["Cut"]

        # Manual result
        arr = np.asarray(img)
        manual = np.ravel(np.mean(arr[points[1]:points[3], points[0]:points[2] + 1], axis=2))

        # Compare
        self.assertEqual(max(app - manual), 0, "Transect on image not accurate at 90 degrees")

    def test_transect_0_deg_nc(self):
        """
        Test an accurate transect is made when taken horizontally on a NetCDF file
        """
        # Setup
        dat = xr.open_dataset(EXAMPLE_3D_PATH)['Theta'].sel(k=-0.5)
        config = {"netcdf": {"x": "i", "y": "j", "z": "k", "z_val": "-0.5", "var": "Theta", "data": dat}}
        points = [100, 50, 200, 50]

        # App result
        app = func.ip_get_points(points, dat.data, config)

        # Manual result
        arr = np.asarray(dat.data)
        manual = arr[points[1]:points[3] + 1, points[0]:points[2]][0]
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
        dat = xr.open_dataset(EXAMPLE_3D_PATH)['Theta'].sel(k=-0.5)
        config = {"netcdf": {"x": "i", "y": "j", "z": "k", "z_val": "-0.5", "var": "Theta", "data": dat}}
        points = [100, 50, 200, 150]

        # App result
        app = func.ip_get_points(points, dat.data, config)

        # Manual result
        arr = np.asarray(dat.data)
        ix = np.arange(points[0], points[2])
        iy = np.arange(points[1], points[3])
        manual = arr[iy, ix]
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
        dat = xr.open_dataset(EXAMPLE_3D_PATH)['Theta'].sel(k=-0.5)
        config = {"netcdf": {"x": "i", "y": "j", "z": "k", "z_val": "-0.5", "var": "Theta", "data": dat}}
        points = [100, 50, 100, 150]

        # App result
        app = func.ip_get_points(points, dat.data, config)

        # Manual result
        arr = np.asarray(dat.data)
        manual = np.ravel(arr[points[1]:points[3], points[0]:points[2] + 1])
        # Compare
        self.assertEqual(max(app["Cut"] - manual), 0, "Transect on NetCDF not accurate at 90 degrees")
        # Check Coordinates from NetCDF
        self.assertListEqual(np.repeat(dat.coords["i"][points[0]].data, len(manual)).tolist(), app["i"],
                             "X Coordinates for NetCDF 90 Degree Transect Incorrect")
        self.assertListEqual(list(dat.coords["j"][points[1]:points[3]]), app["j"],
                             "Y Coordinates for NetCDF 90 Degree Transect Incorrect")

    def test_orthogonal_chain_find(self):
        """
        Test whether valid project files can be accurately identified
        """
        # Data from a valid file is correctly extracted
        proper_json = open(PROJECT_EXAMPLE_PATH)
        proper_data = json.load(proper_json)
        chain_result = orthogonal_chain_find(proper_data, [], ["Click x", "Click y", "Width"])
        self.assertEqual(len(chain_result), len(proper_data["Vorticity"].keys()) - 1, "All chains weren't found")
        self.assertEqual(len(chain_result[0]), 3, "All fields weren't found")
        self.assertListEqual(chain_result[0][0], proper_data["Vorticity"]["Orthogonal Chain 1"]["Click x"],
                             "X Coords were not correct")
        self.assertListEqual(chain_result[1][1], proper_data["Vorticity"]["Orthogonal Chain 2"]["Click y"],
                             "Y coords were not orrect")
        self.assertListEqual(chain_result[2][2], proper_data["Vorticity"]["Orthogonal Chain 3"]["Width"],
                             "Transect widths were not correct")

        # Output data from non-orthogonal chain tool fails
        multi_data = {"Multi": {"Cut 1": {"x": [1000, 2000, 3000], "y": [100, 200, 300], "Cut": [5, 10, 15]},
                                "Cut 2": {"x": [50, 60, 70, 80], "y": [20, 15, 10, 5], "Cut": [33, 66, 99]}}}
        multi_result = orthogonal_chain_find(multi_data, [], ["Click x", "Click y", "Width"])
        self.assertEqual(len(multi_result), 0, "Files that were outputs from Transect tool should fail")

        # All identified chains are unique
        multi_var = {"2nd Var": proper_data["Vorticity"], "Vorticity": proper_data["Vorticity"]}
        multi_var_result = orthogonal_chain_find(multi_var, [], ["Click x", "Click y", "Width"])
        self.assertEqual(len(multi_var_result), len(proper_data["Vorticity"].keys()) - 1, "No repeated chains")

        # Orthogonal chains without all necessary fields aren't included
        del proper_data["Vorticity"]["Orthogonal Chain 1"]["Click x"]
        incomplete_chain_result = orthogonal_chain_find(proper_data, [], ["Click x", "Click y", "Width"])

        self.assertEqual(len(incomplete_chain_result), 2,
                         "Incomplete orthogonal chains should not be included in findings")

        # A random dictionary fails
        bad_data = {"Apples": ["Fuji", "Cosmic Crisp", "Honeycrisp"]}
        bad_data_result = orthogonal_chain_find(bad_data, [], ["Click x", "Click y", "Width"])

        self.assertEqual(bad_data_result, [], "Random dictionaries shouldn't pass")

        # Orthogonal chain coordinates must match current NetCDF file
        wrong_coords_result = orthogonal_chain_find(proper_data, [], ["Click Lon", "Click Lat", "Width"])
        self.assertEqual(len(wrong_coords_result), 0,
                         "Orthogonal chains whose coords don't match current NetCDF file shouldn't be loaded")

    def test_transect_from_points(self):
        """
        Test whether correct netcdf data is collected from user configurations, subset around transect is properly
        calculated, and correct transect is taken. Tested against xarray's interpolation function.
        """
        netcdf_dat = xr.open_dataset(EXAMPLE_3D_PATH)
        points = [87.987, 694.706, 484.004, 596.626]
        f_config = {"netcdf": {"data": netcdf_dat, "x": "i", "y": "k", "z": "j", "z_val": "2780", "var": "Theta"}}
        config = f_config["netcdf"]
        dat, sub_points, sub_scales = func.subset_around_transect(config, points)
        val_dict = func.ip_get_points(sub_points, dat, f_config)
        val_dict[config["x"]] = [x + sub_scales[0] for x in val_dict[config["x"]]]
        val_dict[config["y"]] = [y + sub_scales[1] for y in val_dict[config["y"]]]
        x = xr.DataArray(val_dict[config["x"]])
        y = xr.DataArray(val_dict[config["y"]])

        x_pix = min(abs(x.data[1:] - x.data[:-1]))
        y_pix = min(abs(y.data[1:] - y.data[:-1]))
        new_x = np.arange(x.data.min(), x.data.max(), x_pix)
        new_y = np.arange(y.data.min(), y.data.max(), y_pix)
        og_x = netcdf_dat[config["x"]].data
        og_y = netcdf_dat[config["y"]].data[::-1]

        sub_x = [og_x[np.searchsorted(og_x, x.data.min()) - 1], og_x[np.searchsorted(og_x, x.data.max())]]
        sub_y = [og_y[np.searchsorted(og_y, y.data.min()) - 1], og_y[np.searchsorted(og_y, y.data.max())]]

        xarray_dat = netcdf_dat[config["var"]].sel(
            {config["z"]: float(config["z_val"]), config["x"]: slice(sub_x[0], sub_x[1]),
             config["y"]: slice(sub_y[1], sub_y[0])})
        xarray_interp = xarray_dat.interp({config["x"]: new_x, config["y"]: new_y})
        xarray_i_data = xarray_interp.sel({config["x"]: xr.DataArray(x), config["y"]: xr.DataArray(y)},
                                          method="nearest")
        p_error = max(abs(xarray_i_data.data - val_dict["Cut"])) / (max(val_dict["Cut"]) - min(val_dict["Cut"]))
        self.assertTrue(p_error < 0.01, "Resulting transect is not within error bound")

    def test_validate_config(self):
        """
        When given a dictionary of configuration values, tests whether the program can identify illegal elements.
        """
        illegal_header = {"graphics_defaults": {"contrast": 0, "line_color": "Blue", "colormap": "viridis",
                                                "circle_size": 5},
                          "netcdf": {"dimension_order": ["z", "y", "x"]},
                          "metadta": {}}
        self.assertFalse(func.validate_config(illegal_header), "Illegal config file headers we're allowed.")
        illegal_sub_header = {"graphics_defaults": {"contrast": 0, "line_color": "Blue", "colormap": "viridis",
                                                    "circle_size": 5},
                              "netcdf": {"dimenson_order": ["z", "y", "x"]},
                              "metadata": {}}
        self.assertFalse(func.validate_config(illegal_sub_header), "Illegal config file sub headers we're allowed.")
        illegal_metadata = {"graphics_defaults": {"contrast": 0, "line_color": "Blue", "colormap": "viridis",
                                                  "circle_size": 5},
                            "netcdf": {"dimension_order": ["z", "y", "x"]},
                            "metadata": {"float_field": 40.2}}
        self.assertFalse(func.validate_config(illegal_metadata), "Illegal config file metadata was allowed.")
        illegal_netcdf = {"graphics_defaults": {"contrast": 0, "line_color": "Blue", "colormap": "viridis",
                                                "circle_size": 5},
                          "netcdf": {"dimension_order": ["z", "a", "x"]},
                          "metadata": {}}
        self.assertFalse(func.validate_config(illegal_netcdf), "Illegal config file dimensions order was allowed.")
        illegal_contrast = {"graphics_defaults": {"contrast": 40, "line_color": "Blue", "colormap": "viridis",
                                                  "circle_size": 5},
                            "netcdf": {"dimension_order": ["z", "y", "x"]},
                            "metadata": {}}
        self.assertFalse(func.validate_config(illegal_contrast), "Illegal config file contrast value was allowed.")
        illegal_line_color = {"graphics_defaults": {"contrast": 0, "line_color": "Purple", "colormap": "viridis",
                                                    "circle_size": 5},
                              "netcdf": {"dimension_order": ["z", "y", "x"]},
                              "metadata": {}}
        self.assertFalse(func.validate_config(illegal_line_color), "Illegal config file line color was allowed.")
        illegal_colormap = {"graphics_defaults": {"contrast": 0, "line_color": "Blue", "colormap": "apple",
                                                  "circle_size": 5},
                            "netcdf": {"dimension_order": ["z", "y", "x"]},
                            "metadata": {}}
        self.assertFalse(func.validate_config(illegal_colormap), "Illegal config file colormap was allowed.")
        illegal_circle_size = {"graphics_defaults": {"contrast": 0, "line_color": "Blue", "colormap": "viridis",
                                                     "circle_size": "7"},
                               "netcdf": {"dimension_order": ["z", "y", "x"]},
                               "metadata": {}}
        self.assertFalse(func.validate_config(illegal_circle_size), "Illegal config file circle size was allowed.")
        illegal_orthogonal_chain_width = {"tool_defaults": {"orthogonal_chain_width": 5000}}
        self.assertFalse(func.validate_config(illegal_orthogonal_chain_width),
                         "Illegal config file orthogonal chain width was allowed.")
        legal_config = {"graphics_defaults": {"contrast": 0, "line_color": "Blue", "colormap": "viridis",
                                              "circle_size": 5},
                        "netcdf": {"dimension_order": ["z", "y", "x"]},
                        "metadata": {}}
        self.assertTrue(func.validate_config(legal_config), "Valid config file was deemed invalid.")


if __name__ == '__main__':
    unittest.main()
