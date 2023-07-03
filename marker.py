"""
Class for a single marker widget.
"""

import kivy.uix as ui
from kivy.metrics import dp
from kivy.graphics import Color, Ellipse, Line
from kivy.uix.label import Label
import platform
import math
import copy
import numpy as np
import functions as func
from singletransect import SingleTransect
from multitransect import MultiTransect


class Marker(ui.widget.Widget):
    # Code for a single marker. Uses a MultiTransect as a base but calculates transects
    # orthogonal to line marked out by user

    def __init__(self, multi, home, **kwargs):
        super(Marker, self).__init__(**kwargs)
        self.clicks = 0
        self.points = []
        if platform.system() == "Darwin":
            self.line_width = dp(1)
            self.c_size = (dp(5), dp(5))
        else:
            self.line_width = dp(2)
            self.c_size = (dp(10), dp(10))
        self.dbtn = 0
        self.nbtn = 0
        self.delete = 0
        self.twidth = 40
        self.multi = multi
        self.base = 0
        self.home = home

    def update_width(self, width):
        # Called by marker width widget to change width for next transect
        self.twidth = width

    def get_orthogonal(self, line):
        # Get a line orthogonal to line drawn by user to use as transect
        xyswap = False
        line = line.points
        if line[0] > line[2]:
            line = [line[2], line[3], line[0], line[1]]

        if line[2] - line[0] == 0:
            m = (line[3] - line[1]) / .001
        else:
            m = (line[3] - line[1]) / (line[2] - line[0])

        if m == 0:
            m = -1 / .001
        else:
            m = -1 / m

        if abs(math.atan(m)) > (math.pi / 4):

            xyswap = True
            line = [line[1], line[0], line[3], line[2]]
            m = 1 / m

        mid = (line[0] + (line[2] - line[0]) / 2, line[1] + (line[3] - line[1]) / 2)

        b = mid[1] - m * mid[0]
        xarr = np.arange(int(mid[0] - self.twidth / 2), int(mid[0] + self.twidth / 2))
        yarr = xarr * m + b

        with self.canvas:
            # Draw points at ends of transect
            Color(.28, .62, .86)
            coords = [xarr[0], yarr[0], xarr[-1], yarr[-1]]
            if xyswap:
                coords = [yarr[0], xarr[0], yarr[-1], xarr[-1]]
            c1 = Ellipse(pos=(coords[0] - self.c_size[0] / 2, coords[1] - self.c_size[1] / 2), size=self.c_size)
            c1 = Ellipse(pos=(coords[2] - self.c_size[0] / 2, coords[3] - self.c_size[1] / 2), size=self.c_size)
        return coords

    def run(self):
        # Calls for popup from base and cleans up
        self.base.marker_points(self.points)
        self.base.popup()
        loc = self.home.ids.view.parent # hand reference down
        loc.remove_widget(self.dbtn)
        loc.remove_widget(loc.children[0])
        self.parent.remove_widget(self.parent.children[0])

    def on_touch_down(self, touch):
        # Draws marker line and points
        par = self.home.img.children[0].children[-2] # what is this grabbing, can it be parented up? reference handed?
        self.clicks += 1
        if self.clicks == 2 and not self.multi:
            self.dbtn = func.RoundedButton(text="Download", pos_hint={'x': .85, 'y': 0.02}, size=(dp(100), dp(30)),
                                           size_hint_x=None, size_hint_y=None)
            self.dbtn.bind(on_press=lambda x: self.run())
            self.home.ids.view.parent.add_widget(self.dbtn)
        with self.canvas:
            # Always adds point when clicked
            Color(.28, .62, .86)
            d = Ellipse(pos=(touch.x - self.c_size[0] / 2, touch.y - self.c_size[1] / 2), size=self.c_size)
            self.points.append((touch.x, touch.y, self.twidth))
        if self.clicks != 1:
            # If 2nd or more click, create a line inbetween click points
            with self.canvas:
                line = Line(points=[self.points[-2][0:2], self.points[-1][0:2]], width=self.line_width)
            # Stores orthogonal line in a SingleTransect which gets stored in base MultiTransect
            x = SingleTransect(buttons=False, home=self.home)
            x.line = copy.copy(line)
            x.line.points = self.get_orthogonal(line)
            self.base.lines.append(x)
        else:
            # If new marker creates MultiTransect base and if part of a MultiMarker adds numbers

            self.base = MultiTransect(home=self.home)
            self.base.remove = False

            if self.multi:

                # Adds marker number
                number = Label(text=str(len(par.children)), pos=(touch.x, touch.y), font_size=30)
                self.add_widget(number)

