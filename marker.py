"""
Class for a single marker widget.
"""

import kivy.uix as ui
from kivy.metrics import dp
from kivy.graphics import Color, Ellipse, Line
from kivy.uix.label import Label
import math
import numpy as np
from kivy.core.window import Window
import functions
from singletransect import SingleTransect
from multitransect import MultiTransect


class Marker(ui.widget.Widget):
    # Code for a single marker. Uses a MultiTransect as a base but calculates transects
    # orthogonal to line marked out by user

    def __init__(self, home, **kwargs):
        super(Marker, self).__init__(**kwargs)
        self.clicks = 0
        self.points = []
        self.twidth = 40
        self.base = 0
        self.curr_line = 0
        self.home = home
        self.size = self.home.img.size
        self.pos = self.home.img.pos
        color = self.home.l_col
        if color == "Blue":
            self.l_color = Color(0.28, 0.62, 0.86)
        elif color == "Green":
            self.l_color = Color(0.39, 0.78, 0.47)
        else:
            self.l_color = Color(0.74, 0.42, 0.13)
        size = home.cir_size
        self.c_size = (dp(size), dp(size))
        self.line_width = dp(size / 5)

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
        xarr = np.arange(int(mid[0] - self.twidth / 2), int(mid[0] + self.twidth / 2 + 1))
        yarr = xarr * m + b
        with self.canvas:
            # Draw points at ends of transect
            Color(self.l_color.r, self.l_color.g, self.l_color.b)
            coords = [xarr[0], yarr[0], xarr[-1], yarr[-1]]
            if xyswap:
                coords = [yarr[0], xarr[0], yarr[-1], xarr[-1]]
            c1 = Ellipse(pos=(coords[0] - self.c_size[0] / 2, coords[1] - self.c_size[1] / 2),
                         size=self.c_size, group=str(self.clicks))
            c1 = Ellipse(pos=(coords[2] - self.c_size[0] / 2, coords[3] - self.c_size[1] / 2),
                         size=self.c_size, group=str(self.clicks))
        return coords

    def del_point(self):
        # Remove most recent point, line, and transect points
        if self.clicks != 1:
            self.base.lines = self.base.lines[:-1]
        else:
            self.remove_widget(self.children[0])
            Window.unbind(mouse_pos=self.draw_line)
        self.points.remove(self.points[-1])
        self.canvas.remove_group(str(self.clicks))
        self.canvas.remove_group(str(self.clicks + 1))
        self.clicks -= 1

    def on_touch_down(self, touch):
        # Draws marker line and points
        if self.home.ids.view.collide_point(*self.home.ids.view.to_widget(*self.to_window(*touch.pos))):
            par = self.home.img.children[0].children[-2]
            self.clicks += 1
            with self.canvas:
                # Always adds point when clicked
                Color(self.l_color.r, self.l_color.g, self.l_color.b)
                d = Ellipse(pos=(touch.x - self.c_size[0] / 2, touch.y - self.c_size[1] / 2),
                            size=self.c_size, group=str(self.clicks))
                self.points.append((touch.x, touch.y, self.twidth))
                self.curr_line = Line(points=[], width=self.line_width, group=str(self.clicks + 1))
            Window.bind(mouse_pos=self.draw_line)
            if self.clicks != 1:
                # If 2nd or more click, create a line inbetween click points
                with self.canvas:
                    line = Line(points=[self.points[-2][0:2], self.points[-1][0:2]],
                                width=self.line_width, group=str(self.clicks))
                # Stores orthogonal line in a SingleTransect which gets stored in base MultiTransect
                coords = self.get_orthogonal(line)
                if self.in_bounds(coords):
                    # Check if orthogonal points are within image bounds
                    x = SingleTransect(home=self.home)
                    x.line = Line(points=[], width=self.line_width)
                    x.line.points = self.get_orthogonal(line)
                    self.base.lines.append(x)
                else:
                    # Undo actions
                    self.canvas.remove_group(str(self.clicks))
                    self.canvas.remove(self.curr_line)
                    self.clicks -= 1
                    self.points = self.points[:-1]
                    functions.alert("Orthogonal point out of bounds", self.home)

            else:
                # If new marker creates MultiTransect base and if part of a MultiMarker adds numbers
                self.base = MultiTransect(home=self.home)

                # Adds marker number
                number = Label(text=str(len(par.children)), pos=(touch.x, touch.y), font_size=30)
                self.add_widget(number)
                # Use width from previous marker
                if len(self.parent.children) > 1:
                    self.twidth = self.parent.children[1].twidth

    def draw_line(self, instance, pos):
        if self.parent.children[0] == self and not self.parent.dragging:
            if self.home.ids.view.collide_point(*self.home.ids.view.to_widget(*pos)):
                mouse = self.to_widget(*pos)
                if self.size[0] >= mouse[0] >= 0 and self.size[1] >= mouse[1] >= 0:
                    with self.canvas:
                        self.curr_line.points = [self.points[-1][0:2], self.to_widget(pos[0], pos[1])]
        else:
            self.stop_drawing()

    def stop_drawing(self):
        with self.canvas:
            self.curr_line.points = self.curr_line.points[0:2]

    def in_bounds(self, points):
        dots = [points[0:2], points[2:4]]
        for d in dots:
            if min(d) < 0 or any([l[0] > l[1] for l in list(zip(d, self.size))]):
                return False
        return True

