"""
Unit tests to insure transect accuracy and protect from invalid file names
"""

import unittest
from PIL import Image as Im
import numpy as np
from pathlib import Path
import xarray as xr
import functions as func


class Test(unittest.TestCase):
    def test_transect_0_deg_img(self):
        # Setup
        img = Im.open("support/example.jpg").convert('RGB')
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
        # Setup
        img = Im.open("support/example.jpg").convert('RGB')
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
        # Setup
        img = Im.open("support/example.jpg").convert('RGB')
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
        # Setup
        dat = xr.open_dataset("support/example.nc")['Divergence'].data
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
        # Setup
        dat = xr.open_dataset("support/example.nc")['Divergence'].data
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
        # Setup
        dat = xr.open_dataset("support/example.nc")['Divergence'].data
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
        # Setup
        rel_path = Path().absolute()

        # Test output file name rules
        self.assertFalse(func.check_file(rel_path, "", ".jpg"), "No blank file name")
        self.assertFalse(func.check_file(rel_path, "test$", ".json"), "No special characters")
        self.assertFalse(func.check_file(rel_path, "support/dir1/dir2/dir3/test", ".json"),
                         "Directories must exist")
        self.assertEqual(func.check_file(rel_path, "test.jpg", ".jpg"), "test",
                         "Remove user entered extensions")
        self.assertEqual(func.check_file(rel_path, "support/example", ".jpg"),
                         "support/example(1)",
                         "If file already exists add (#)")


if __name__ == '__main__':
    unittest.main()
