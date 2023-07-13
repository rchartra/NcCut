"""
Unit tests for CutView app
"""

import unittest
import os
import time
import numpy as np
import json
from functools import partial
import kivy
from kivy.graphics import Line
from kivy.clock import Clock

import functions
from imageview import ImageView
from singletransect import SingleTransect
from multimarker import MultiMarker, Click
from multitransect import MultiTransect
from markerwidth import MarkerWidth
from marker import Marker
from functions import RoundedButton
from cutview import CutView


class AppInfo:
    def __init__(self):
        self.home = None

    def hold_home(self, home):
        self.home = home


run_app = AppInfo()


def pause():
    time.sleep(0.000001)


def run_tests(app, *args):
    Clock.schedule_interval(pause, 0.000001)
    app.stop()
    run_app.hold_home(app.root.get_screen("HomeScreen"))


def get_app():
    app = CutView()
    p = partial(run_tests, app)
    Clock.schedule_once(p, 0.000001)
    app.run()


class Test(unittest.TestCase):
    # tests go button creates image viewer

    @classmethod
    def setUpClass(cls):
        get_app()

    def get_gui_single_result(self, start, end):
        transect = run_app.home.img.children[0].children[0]
        win = kivy.core.window.Window
        transect.on_touch_down(start)
        transect.on_touch_down(end)
        transect.popup.content.children[0].children[1].dispatch("on_press")
        win.children[0].content.children[1].text = "__test"
        win.children[0].content.children[0].dispatch("on_press")
        win.children[0].content.children[0].dispatch("on_release")
        f = open("__test.json")
        dat = json.load(f)['Cut']
        f.close()
        os.remove("__test.json")
        return dat

    def single_transect_tests(self):

        # check transect is created
        run_app.home.transectbtn("single")
        transect = run_app.home.img.children[0].children[0]
        self.assertTrue(isinstance(transect, SingleTransect), "Single transect widget created")

        if run_app.home.nc:
            arr = np.asarray(run_app.home.data)
        else:
            arr = np.asarray(run_app.home.rgb)
        rows = np.shape(arr)[0]  # numpy arrays are indexed by row, column NOT x, y

        # test transect at zero degree angle
        # ---------------------------------
        zstart = Click(1000, 200)
        zend = Click(1200, 200)

        data = self.get_gui_single_result(zstart, zend)

        # manual transect
        if run_app.home.nc:
            manual = arr[rows - zend.y - 1:rows - zstart.y, zstart.x:zend.x][0]
        else:
            manual = np.ravel(np.mean(arr[rows - zend.y - 1:rows - zstart.y, zstart.x:zend.x], axis=2))

        # compare
        self.assertEqual(max(data - manual), 0, "Transect accurate at zero degrees")

        # test transect at 45 degree angle
        # -------------------------------
        run_app.home.transectbtn("single")

        fstart = Click(1000, 200)
        fend = Click(1200, 400)

        data = self.get_gui_single_result(fstart, fend)

        # manual transect
        ix = np.arange(fstart.x, fend.x)
        iy = np.arange(fstart.y, fend.y)
        if run_app.home.nc:
            manual = arr[rows - iy - 1, ix]
        else:
            manual = np.ravel(np.mean(arr[rows - iy - 1, ix], axis=1))

        # compare
        self.assertEqual(max(data - manual), 0, "Transect accurate at 45 degrees")

        # test transect at 90 degree angle
        # ---------------------------------
        run_app.home.transectbtn("single")

        nstart = Click(1000, 100)
        nend = Click(1000, 400)

        data = self.get_gui_single_result(nstart, nend)

        # manual transect
        if run_app.home.nc:
            manual = np.ravel(np.flip(arr[rows - nend.y:rows - nstart.y, nstart.x:nend.x + 1]))
        else:
            manual = np.ravel(np.mean(np.flip(arr[rows - nend.y:rows - nstart.y, nstart.x:nend.x + 1]), axis=2))

        # compare
        self.assertEqual(max(data - manual), 0, "Transect accurate at 90 degrees")
        # check clean up
        self.assertEqual(len(run_app.home.img.children[0].children), 1, "Viewre cleaned")

    def multi_transect_tests(self):
        # check transect created
        run_app.home.transectbtn("multi")
        transect = run_app.home.img.children[0].children[0]
        self.assertTrue(isinstance(transect, MultiTransect), "Multi transect widget created")

        clicks = [Click(20, 120), Click(50, 150), Click(80, 180), Click(110, 210)]
        for c in clicks:
            transect.on_touch_down(c)

        # check lines and buttons
        self.assertEqual(len(transect.lines), 2, "Multiple transects created")
        self.assertTrue(any(isinstance(x, RoundedButton) for x in run_app.home.ids.view.parent.children),
                        "Buttons present when all transects are completed")

        transect.on_touch_down(Click(140, 240))

        self.assertEqual(len(transect.lines), 3, "New transects created")
        self.assertFalse(any(isinstance(x, RoundedButton) for x in run_app.home.ids.view.parent.children),
                         "Buttons not present when not all transects are completed")

        # check clean up
        run_app.home.transectbtn("multi")
        self.assertEqual(len(run_app.home.ids.view.parent.children), 1, "All buttons cleared")
        self.assertEqual(len(run_app.home.img.children[0].children), 1, "All transects cleared")

    def marker_tests(self):
        # check transect created
        run_app.home.transectbtn("marker")
        transect = run_app.home.img.children[0].children[0]
        self.assertTrue(isinstance(transect, Marker), "Marker widget created")

        # check width updating
        wth = run_app.home.ids.view.parent.children[0]
        self.assertTrue(isinstance(wth, MarkerWidth), "Marker width adjustment widget created")
        wth.txt.text = "50"
        wth.btn.dispatch("on_press")
        self.assertEqual(transect.twidth, 50, "Marker width updates")

        # check orthogonal
        line = Line(points=[50, 50, 100, 100])
        coords = np.array(transect.get_orthogonal(line))
        self.assertEqual(max(coords - [50, 100, 100, 50]), 0, "Marker creates transects orthogonal to user clicks")

        # check download button
        transect.on_touch_down(Click(50, 50))
        self.assertFalse(any(isinstance(x, RoundedButton) for x in run_app.home.ids.view.parent.children),
                         "No download when only one point")
        transect.on_touch_down(Click(100, 100))
        self.assertTrue(any(isinstance(x, RoundedButton) for x in run_app.home.ids.view.parent.children),
                        "Download once at least one transect exists")

        # check transects
        self.assertEqual(len(transect.base.lines), 1, "2 clicks creates one transect")
        transect.on_touch_down(Click(150, 150))
        self.assertEqual(len(transect.base.lines), 2, "3 clicks creates two transects")

        # check clean up
        run_app.home.transectbtn("marker")
        self.assertEqual(len(run_app.home.ids.view.parent.children), 1, "All buttons cleared")
        self.assertEqual(len(run_app.home.img.children[0].children), 1, "All transects cleared")

    def multi_marker_tests(self):
        # check transect created
        run_app.home.transectbtn("filament")
        transect = run_app.home.img.children[0].children[0]
        self.assertTrue(isinstance(transect, MultiMarker), "MultiMarker widget created")
        btn_loc = run_app.home.ids.view.parent.children

        # check initial buttons
        self.assertEqual(len([x for x in btn_loc if isinstance(x, RoundedButton)]), 3, "Initial buttons add")

        # first click widgets
        transect.on_touch_down(Click(50, 50))
        self.assertEqual(len([x for x in btn_loc if isinstance(x, RoundedButton)]), 3, "No download on first click")
        self.assertTrue(any(isinstance(x, MarkerWidth) for x in btn_loc), "Marker width on first click")

        # second click widgets
        transect.on_touch_down(Click(100, 100))
        self.assertEqual(len([x for x in btn_loc if isinstance(x, RoundedButton)]), 4, "Download button adds")
        self.assertEqual(transect.children[0].children[0].text, "1", "Correct marker labels")

        # new line button
        transect.nbtn.dispatch("on_press")
        transect.nbtn.dispatch("on_press")
        self.assertEqual(len(transect.children), 2, "If line has no clicks don't make more lines")

        # delete button
        transect.on_touch_down(Click(100, 200))
        transect.on_touch_down(Click(150, 230))
        transect.delete.dispatch("on_press")
        self.assertEqual(len(transect.children), 2, "Delete and add new line")
        transect.on_touch_down(Click(100, 200))
        transect.on_touch_down(Click(150, 230))
        transect.nbtn.dispatch("on_press")
        transect.delete.dispatch("on_press")
        self.assertEqual(len(transect.children), 2, "Delete empty new line and prev line")
        transect.delete.dispatch("on_press")
        transect.delete.dispatch("on_press")
        self.assertEqual(len(transect.children), 1, "Always able to draw right away")
        self.assertEqual(len([x for x in btn_loc if isinstance(x, RoundedButton)]), 3, "Deleting reverts buttons")

        # marker width
        transect.on_touch_down(Click(100, 200))
        transect.on_touch_down(Click(150, 230))
        transect.width_w.txt.text = "50"
        transect.width_w.btn.dispatch("on_press")
        self.assertEqual(transect.children[0].twidth, 50, "Width changing works")
        transect.nbtn.dispatch("on_press")
        transect.on_touch_down(Click(100, 200))
        transect.on_touch_down(Click(150, 230))
        self.assertEqual(transect.children[0].twidth, 50, "New marker uses previous marker width as default")

        # file structure
        transect.on_touch_down(Click(200, 260))

        transect.dbtn.dispatch("on_press")

        kivy.core.window.Window.children[0].content.children[1].text = "___test"
        kivy.core.window.Window.children[0].content.children[0].dispatch("on_press")
        kivy.core.window.Window.children[0].content.children[0].dispatch("on_release")
        f = open("___test.json")
        dat = json.load(f)
        f.close()
        os.remove("___test.json")
        self.assertEqual(list(dat.keys()), ["Marker 1", "Marker 2"], "All markers download")
        self.assertEqual(list(dat["Marker 2"].keys()),
                         ['Click X', 'Click Y', 'Width', 'Cut 1', 'Cut 2'],
                         "All fields downloaded")
        self.assertEqual(dat['Marker 2']['Width'], [40, 50, 50], "Marker widths downloaded")
        self.assertEqual(dat['Marker 2']['Click X'], [100, 150, 200], "Marker clicks downloaded")

        # clean up
        run_app.home.transectbtn("filament")
        self.assertEqual(len(run_app.home.ids.view.parent.children), 1)
        self.assertEqual(len(run_app.home.img.children[0].children), 1)

        # upload project
        run_app.home.transectbtn("filament")
        transect = run_app.home.img.children[0].children[0]
        transect.upbtn.dispatch("on_press")
        kivy.core.window.Window.children[0].content.children[1].text = "support/example_markers.json"
        kivy.core.window.Window.children[0].content.children[0].dispatch("on_release")
        self.assertEqual(len(transect.children), 10, "All markers upload")
        transect.on_touch_down(Click(100, 200))
        self.assertEqual(len(transect.children), 11, "Start out on new marker")

    def rotation_test(self):
        run_app.home.rotate()
        self.assertEqual(run_app.home.img.rotation, 45, "Viewer rotates 45 deg")

    def test_file_names(self):
        # check error messages for file input
        run_app.home.ids.file_in.text = "\\\\"
        run_app.home.gobtn()
        self.assertEqual(run_app.home.children[0].text, "Invalid File Name", "Backslashes don't crash GUI")
        run_app.home.ids.file_in.text = "*$%&@! "
        run_app.home.gobtn()
        self.assertEqual(run_app.home.children[0].text, "Invalid File Name", "No irregular characters")
        run_app.home.ids.file_in.text = ""
        run_app.home.gobtn()
        self.assertEqual(run_app.home.children[0].text, "Invalid File Name", "No empty file names")

        # download file name checks
        self.assertFalse(functions.check_file("", ".jpg"), "No blank file name")
        self.assertFalse(functions.check_file("test$", ".json"), "No special characters")
        self.assertFalse(functions.check_file("support/dir1/dir2/dir3/test", ".json"), "Directories must exist")
        self.assertEqual(functions.check_file("test.jpg", ".jpg"), "test", "Remove user entered extensions")
        self.assertEqual(functions.check_file("support/example", ".jpg"),
                         "support/example(1)",
                         "If file already exists add (#)")

    def test_img_transects(self):
        # runs all tests for images
        run_app.home.ids.file_in.text = "support/example.jpg"
        run_app.home.gobtn()
        self.assertTrue(isinstance(run_app.home.img, ImageView))

        self.single_transect_tests()
        self.multi_transect_tests()
        self.marker_tests()
        self.multi_marker_tests()
        self.rotation_test()

    def test_nc_transects(self):
        # runs all tests for nc files
        run_app.home.ids.file_in.text = "support/example.nc"
        run_app.home.gobtn()
        # select dataset
        kivy.core.window.Window.children[0].content.children[0].dispatch("on_press")
        kivy.core.window.Window.children[0].content.children[0].dispatch("on_release")
        self.assertTrue(isinstance(run_app.home.img, ImageView))

        self.single_transect_tests()
        self.multi_transect_tests()
        self.marker_tests()
        self.multi_marker_tests()
        self.rotation_test()


if __name__ == '__main__':
    unittest.main()
