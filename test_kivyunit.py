import unittest

import os
import sys
import time
import os.path as op
from functools import partial
from kivy.clock import Clock
from kivy.tests.common import GraphicUnitTest

from kivy.input.motionevent import MotionEvent
from kivy.base import EventLoop

from cutview import cutview
from multimarker import MultiMarker


class UTMotionEvent(MotionEvent):
    def depack(self, args):
        self.is_touch = True
        self.sx = args['sx']
        self.sy = args['sy']
        self.profile = ['pos']
        super(UTMotionEvent, self).depack(args)

#
# class MultiMarkerTestCase(GraphicUnitTest):
#     framecount = 0
#
#     # debug test with / stop destroying window
#     # def tearDown(self, *_): pass
#     # def setUp(self, *_): pass
#
#     def test_single_button(self):
#         # get Window instance for creating visible
#         # widget tree and for calculating coordinates
#         EventLoop.ensure_window()
#         win = EventLoop.window
#
#         # add widget for testing
#
#         # get widgets ready
#         EventLoop.idle()
#
#         touch = UTMotionEvent(sx=0.8, sy=0.9)
#
#         EventLoop.post_dispatch_input("begin", touch)
#         EventLoop.post_dispatch_input("end", touch)
#
#         self.assertTrue(x = app.root.get_screen("HomeScreen").ids)


class Test(unittest.TestCase):
    # sleep function that catches ``dt`` from Clock
    def pause(*args):
        time.sleep(0.000001)

    # main test function
    def run_tests(self, app, *args):
        Clock.schedule_interval(self.pause, 0.000001)

        # Do something
        # Comment out if you are editing the test, it'll leave the
        # Window opened.
        app.stop()

        x = app.root.get_screen("HomeScreen").ids.view.children
        self.go_button_test(app)

        self.assertTrue(len(x) >= 0)

    # same named function as the filename(!)
    def test_kivyunit(self):
        app = cutview()
        p = partial(self.run_tests, app)
        Clock.schedule_once(p, 0.000001)
        app.run()

    def go_button_test(self, app):
        EventLoop.ensure_window()
        win = EventLoop.window

        home = app.root.get_screen("HomeScreen")

        home.ids.file_in.text = "support/example.jpg"
        home.gobtn()

        # get widgets ready
        EventLoop.idle()

        # go button press
        touch = UTMotionEvent("unittest", 1, {"sx": 0.56, "sy": 0.052})

        EventLoop.post_dispatch_input("begin", touch)
        EventLoop.post_dispatch_input("end", touch)

        self.assertTrue(home.fileon == True)


if __name__ == '__main__':
    unittest.main()