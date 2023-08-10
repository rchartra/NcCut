"""
Class for a singular transect
"""

import kivy.uix as ui
from kivy.graphics import Color, Ellipse, Rectangle, Line
from kivy.metrics import dp
from kivy.uix.label import Label
from kivy.core.window import Window
import numpy as np
import math
from scipy import interpolate


class SingleTransect(ui.widget.Widget):
    # Base code for any single transect
    def __init__(self, home, **kwargs):
        super(SingleTransect, self).__init__(**kwargs)
        self.line = Line()
        self.circles = 0
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

    def ip_get_points(self):
        # Creates a data frame containing x, y, and value of points on transect line
        # If angle of line is > 45 degrees will swap x and y to still get an accurate answer
        r = 0
        data = []
        xyswap = False

        # Gather data as array
        if self.home.nc:
            img = self.home.data
        else:
            img = self.home.rgb
        line = self.line.points
        # Always read from left point to right
        if line[0] > line[2]:
            line = [line[2], line[3], line[0], line[1]]

        # Get interpolation object

        # Get x values
        ix = np.arange(int(line[0] - 3), int(line[2] + 4))
        # Get y values increasing in value w/o changing og object
        if line[1] > line[3]:
            iy = np.arange(int(line[3] - 3), int(line[1] + 4))
        else:
            iy = np.arange(int(line[1] - 3), int(line[3] + 4))
        # Get line slope
        if line[2] - line[0] == 0:
            m = (line[3] - line[1]) / .001
        else:
            m = (line[3] - line[1]) / (line[2] - line[0])
        # If slope greater than 45 deg swap xy
        if abs(math.atan(m)) > (math.pi / 4):
            xyswap = True
            line = [line[1], line[0], line[3], line[2]]
            # Recalculate slope with new order
            if line[2] - line[0] == 0:
                m = (line[3] - line[1]) / .001
            else:
                m = (line[3] - line[1]) / (line[2] - line[0])
        b = line[1] - m * (line[0])
        imgA = np.asarray(img)
        z = imgA[-(iy[-1] + 1):-(iy[0]), ix[0]:ix[-1] + 1]
        if not self.home.nc:
            # If image, take average of RGB values as point value
            z = np.mean(z, axis=2)
        z = np.flipud(z)
        # numpy arrays are indexed by row, column NOT x, y, but interp object does do x y
        int_pol = interpolate.interp2d(ix, iy, z, kind='linear')

        if line[0] > line[2]:
            xarr = np.arange(int(line[2]), int(line[0]))
        else:
            xarr = np.arange(int(line[0]), int(line[2]))
        yarr = xarr * m + b

        # Grab points from interpolation object
        for i in range(0, xarr.size):
            if xyswap:
                data.append(int_pol(yarr[i], xarr[i])[0])
            else:
                data.append(int_pol(xarr[i], yarr[i])[0])
        if xyswap:
            data = {'x': yarr, 'y': xarr, 'Cut': data}
        else:
            data = {'x': xarr, 'y': yarr, 'Cut': data}
        data = {'x': data['x'].tolist(), 'y': data['y'].tolist(), 'Cut': data['Cut']}

        return data

    def on_touch_down(self, touch):
        # Gathering touch coordinates and display line graphics
        if self.home.ids.view.collide_point(*self.home.ids.view.to_widget(*self.to_window(*touch.pos))):
            if self.circles == 0:
                self.circles += 1
                number = Label(text=str(len(self.parent.children)), pos=(touch.x, touch.y), font_size=30)
                self.add_widget(number)
                with self.canvas:
                    Color(self.l_color.r, self.l_color.g, self.l_color.b)
                    self.line = Line(points=[], width=self.line_width)
                    c1 = Ellipse(pos=(touch.x - self.c_size[0] / 2, touch.y - self.c_size[1] / 2), size=self.c_size)
                    self.line.points = (touch.x, touch.y)
                Window.bind(mouse_pos=self.draw_line)

            elif self.circles == 1:
                # If clicked the same point as before, do nothing
                self.circles += 1
                if len(self.line.points) != 2:
                    self.line.points.pop()
                    self.line.points.pop()
                if [touch.x, touch.y] == self.line.points:
                    return
                with self.canvas:
                    c2 = Ellipse(pos=(touch.x - self.c_size[0] / 2, touch.y - self.c_size[1] / 2), size=self.c_size)
                    self.line.points += (touch.x, touch.y)

    def draw_line(self, instance, pos):
        if self.home.ids.view.collide_point(*self.home.ids.view.to_widget(*pos)):
            mouse = self.to_widget(*pos)
            if self.size[0] >= mouse[0] >= 0 and self.size[1] >= mouse[1] >= 0:
                if self.circles == 1:
                    if len(self.line.points) == 2:
                        with self.canvas:
                            self.line.points += self.to_widget(pos[0], pos[1])
                    else:
                        self.line.points.pop()
                        self.line.points.pop()
                        with self.canvas:
                            self.line.points += self.to_widget(pos[0], pos[1])

