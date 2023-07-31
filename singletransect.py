"""
Class for singular transect tool. Additionally, contains much of the base download and popup functionality.
"""

import kivy
import kivy.uix as ui
from kivy.graphics import Color, Ellipse, Line
from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
import numpy as np
import math
import pandas as pd
import os
import json
import platform
from scipy import interpolate
import functions as func


class SingleTransect(ui.widget.Widget):
    # Base code for any single transect
    def __init__(self, buttons, home, **kwargs):
        super(SingleTransect, self).__init__(**kwargs)
        self.btns = buttons
        self.line = Line()
        self.circles = 0
        self.home = home
        self.btn = Button()
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
        self.plot = 0
        self.popup = 0
        self.data = 0

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
        intPol = interpolate.interp2d(ix, iy, z, kind='linear')

        if line[0] > line[2]:
            xarr = np.arange(int(line[2]), int(line[0]))
        else:
            xarr = np.arange(int(line[0]), int(line[2]))
        yarr = xarr * m + b

        # Grab points from interpolation object
        for i in range(0, xarr.size):
            if xyswap:
                data.append(intPol(yarr[i], xarr[i])[0])
            else:
                data.append(intPol(xarr[i], yarr[i])[0])
        if xyswap:
            data = {'x': yarr, 'y': xarr, 'Cut': data}
        else:
            data = {'x': xarr, 'y': yarr, 'Cut': data}
        data = {'x': data['x'].tolist(), 'y': data['y'].tolist(), 'Cut': data['Cut']}

        return data

    def file_input(self, dat, type):
        # Popup window for input of name for plot/json file
        content = ui.boxlayout.BoxLayout(orientation='horizontal')
        popup = Popup(title="File Name", content=content, size_hint=(0.5, 0.15))
        txt = TextInput(size_hint=(0.7, 1), hint_text="Enter File Name")
        content.add_widget(txt)
        go = Button(text="Ok", size_hint=(0.3, 1))
        if type == "data":
            go.bind(on_press=lambda x: self.download_data(dat, txt.text))
        else:
            go.bind(on_press=lambda x: self.download_plot(dat, txt.text))
        go.bind(on_release=lambda x: self.close_popups(popup))
        content.add_widget(go)
        popup.open()

    def close_popups(self, fpop):
        # Close file name popup and plot popup
        fpop.dismiss()
        self.popup.dismiss()

    def download_plot(self, dat, fname):
        # Code to make and download plot of a single transect
        func.plotdf(dat, self.home)
        file = func.check_file(self.home.rel_path, fname, ".jpg")
        if file is False:
            func.alert("Invalid File Name", self.home)
            os.remove("____.jpg")
            return
        else:
            path = self.home.rel_path / (file + ".jpg")
            os.rename("____.jpg", str(path))
            func.alert("Download Complete", self.home)

    def download_data(self, dat, fname):
        # Downloads data into a json file
        file = func.check_file(self.home.rel_path, fname, ".json")
        if file is False:
            func.alert("Invalid File Name", self.home)
            return
        else:
            # To json code
            with open(self.home.rel_path / (file + ".json"), "w") as f:
                json.dump(dat, f)

            func.alert("Download Complete", self.home)

    def plot_popup(self, dat):
        # Opens popup window with plot and download options
        content = ui.boxlayout.BoxLayout(orientation='vertical', spacing=10)
        func.plotdf(dat, self.home)
        self.popup = Popup(title="Transect", content=content, size_hint=(0.8, 0.8))
        self.plot = ui.image.Image(source='____.jpg', size_hint=(1, .9))
        self.plot.reload()
        content.add_widget(self.plot)
        os.remove("____.jpg")
        btns = ui.boxlayout.BoxLayout(orientation='horizontal', size_hint=(1, .1), spacing = 5)

        dbtn = func.RoundedButton(text="Download to JSON", size_hint=(.5, 1))
        dbtn.bind(on_press=lambda x: self.file_input(dat, 'data'))

        ibtn = func.RoundedButton(text='Download Plot', size_hint=(.5, 1))
        ibtn.bind(on_press=lambda x: self.file_input(dat, 'plot'))

        btns.add_widget(dbtn)
        btns.add_widget(ibtn)
        content.add_widget(btns)

        self.line.points = []
        self.home.tMode = False
        kivy.core.window.Window.set_system_cursor("arrow")
        self.popup.open()

    def on_touch_down(self, touch):
        # Gathering touch coordinates and display line graphics
        if (self.circles < 1):
            self.circles += 1
            with self.canvas:
                Color(self.l_color.r, self.l_color.g, self.l_color.b)
                self.line = Line(points=[], width=self.line_width)
                c1 = Ellipse(pos=(touch.x - self.c_size[0] / 2, touch.y - self.c_size[1] / 2), size=self.c_size)
                self.line.points = (touch.x, touch.y)

        elif (self.circles < 2):
            # If clicked the same point as before, do nothing
            if [touch.x, touch.y] == self.line.points:
                return
            self.circles += 1
            with self.canvas:
                c2 = Ellipse(pos=(touch.x - self.c_size[0] / 2, touch.y - self.c_size[1] / 2), size=self.c_size)
                self.line.points += (touch.x, touch.y)

            if self.btns:
                # For when just a single transect, doesn't do buttons if just a base for a higher tool
                dat = self.ip_get_points()
                self.plot_popup(dat)
                while len(self.parent.children) > 2:
                    self.parent.remove_widget(self.parent.children[0])
                self.parent.remove_widget(self.parent.children[0])
