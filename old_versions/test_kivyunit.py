import unittest

import time
import os
import numpy as np
import json
from functools import partial
from kivy.clock import Clock
import kivy

from kivy.tests.common import GraphicUnitTest
from kivy.input.motionevent import MotionEvent
from kivy.base import EventLoop

from cutview import cutview
from imageview import ImageView
from singletransect import SingleTransect
from multimarker import MultiMarker, Click
import unit_testing


class Test(unittest.TestCase):

    # sleep function that catches ``dt`` from Clock
    def pause(*args):
        time.sleep(0.000001)

    # main test function
    def run_tests(self, app, *args):
        Clock.schedule_interval(self.pause, 0.00001)
        app.stop()
        home = app.root.get_screen("HomeScreen")

        suite = unittest.TestLoader().loadTestsFromModule(unit_testing)
        # run all tests with verbosity
        unittest.TextTestRunner(verbosity=2).run(suite)
        app.stop()

    # same named function as the filename
    def test_kivyunit(self):
        app = cutview()
        p = partial(self.run_tests, app)
        Clock.schedule_once(p, 0.000001)
        app.run()

    # # tests go button creates image viewer
    # def go_button_test(self):
    #     Clock.schedule_once(self.pause, 0.00001)
    #     self.home.ids.file_in.text = "support/example.jpg"
    #     self.home.gobtn()
    #
    #     self.assertTrue(isinstance(self.home.img, ImageView))
    #
    # def single_transect_tests(self):
    #
    #     # check transect is created
    #     self.home.transectbtn("single")
    #     transect = self.home.img.children[0].children[0]
    #     self.assertTrue(isinstance(transect, SingleTransect))
    #
    #     arr = np.asarray(self.home.rgb)
    #     rows = np.shape(arr)[0]  # numpy arrays are indexed by row, column NOT x, y
    #
    #     # test transect at zero degree angle
    #     # ---------------------------------
    #     zstart = Click(1000, 200)
    #     zend = Click(1200, 200)
    #
    #     data = self.get_gui_single_result(zstart, zend)
    #
    #     # manual transect
    #     manual = np.ravel(np.mean(arr[rows - zend.y - 1:rows - zstart.y, zstart.x:zend.x], axis=2))
    #
    #     # compare
    #     self.assertEqual(max(data - manual), 0)
    #
    #     # test transect at 45 degree angle
    #     # -------------------------------
    #     self.home.transectbtn("single")
    #
    #     fstart = Click(1000, 200)
    #     fend = Click(1200, 400)
    #
    #     data = self.get_gui_single_result(fstart, fend)
    #
    #     # manual transect
    #     ix = np.arange(fstart.x, fend.x)
    #     iy = np.arange(fstart.y, fend.y)
    #     manual = np.ravel(np.mean(arr[rows - iy - 1, ix], axis=1))
    #
    #     # compare
    #     self.assertEqual(max(data - manual), 0)
    #
    #     # test transect at 90 degree angle
    #     # ---------------------------------
    #     self.home.transectbtn("single")
    #
    #     nstart = Click(1000, 100)
    #     nend = Click(1000, 400)
    #
    #     data = self.get_gui_single_result(nstart, nend,)
    #
    #     # manual transect
    #     manual = np.ravel(np.mean(np.flip(arr[rows - nend.y:rows - nstart.y, nstart.x:nend.x + 1]), axis=2))
    #
    #     # compare
    #     self.assertEqual(max(data - manual), 0)
    #
    # def single_transect_nc_test(self):
    #     self.home.ids.file_in.text = "support/example.nc"
    #     self.home.gobtn()
    #
    #     self.assertTrue(self.home.nc)
    #
    # def get_gui_single_result(self, start, end):
    #     transect = self.home.img.children[0].children[0]
    #     win = kivy.core.window.Window
    #     transect.on_touch_down(start)
    #     transect.on_touch_down(end)
    #     transect.popup.content.children[0].children[1].dispatch("on_press")
    #     win.children[0].content.children[1].text = "__test"
    #     win.children[0].content.children[0].dispatch("on_press")
    #     win.children[0].content.children[0].dispatch("on_release")
    #     f = open("__test.json")
    #     dat = json.load(f)['Cut']
    #     f.close()
    #     os.remove("__test.json")
    #     return dat


if __name__ == '__main__':
    unittest.main()