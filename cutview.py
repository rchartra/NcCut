from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Color, Ellipse, Line
from kivy.graphics.transformation import Matrix
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.metrics import dp

import kivy
import kivy.uix as ui

from functools import partial
import pandas as pd
import matplotlib.pyplot as plt
from scipy import interpolate
import numpy as np
from PIL import Image as im
import xarray as xr
import math
import copy
import platform
import os
import time
from os.path import exists
from cmaps import _viridis_data



def removeAlert(alert, *largs):
    root.get_screen("HomeScreen").ids.view.parent.remove_widget(alert)

def alert(text):
    alert = Button(text=text, size_hint=(0.25, 0.1), pos_hint={'x': 0.01, 'y': 0.89}, disabled=True)
    root.get_screen("HomeScreen").ids.view.parent.add_widget(alert)
    kivy.clock.Clock.schedule_once(partial(removeAlert, alert), 2)

def plotdf(df, nc):
    # General Plotting Code
    ndf = pd.DataFrame()

    for i in df.columns:
        if i[0:3] == "Cut":
            ndf[i] = df[i]
    x = np.asarray(ndf.index)
    ndf.index = (x - x[0]) / (x[-1] - x[0])
    plt.plot(ndf)
    if nc:
        plt.ylabel(root.get_screen("HomeScreen").ds.capitalize())
    else:
        plt.ylabel("Mean RGB Value")
        plt.gca().set_ylim(ymin=0)
    plt.xlabel("Normalized Long Transect Distance")
    plt.legend(ndf.columns, title="Legend", bbox_to_anchor=(1.05, 1))
    plt.tight_layout()
    plt.savefig("____.jpg")
    plt.close('all')

class RoundedButton(Button):
     pass

class HomeScreen(Screen):
    # Main screen functionality
    def __init__(self, **kwargs):
        super(HomeScreen, self).__init__(**kwargs)
        self.fileon = False
        self.img = 0
        self.transect = SingleTransect(buttons=True, nc=False)
        self.tMode = False
        self.data = 0
        self.ds = 0
        self.nc = False
        self.file = 0

    def transectbtn(self, type):
        # Manages the creation and deletion of each tool
        if self.fileon:
            if not self.tMode:
                # Opens a new tool
                kivy.core.window.Window.set_system_cursor("crosshair")
                if type == "single":
                    self.transect = SingleTransect(buttons=True, nc=self.nc)
                elif type == "multi":
                    self.transect = MultiTransect()
                elif type == "filament":
                    self.transect = MultiMarker()
                    self.ids.view.parent.add_widget(MarkerWidth(self.transect,
                                                                size_hint=(0.15, 0.06),
                                                                orientation='horizontal',
                                                                pos_hint={'x': 0.01, 'y': 0.01}))
                else:
                    self.transect = Marker(nc=self.nc, multi=False)
                    self.ids.view.parent.add_widget(MarkerWidth(self.transect,
                                                                size_hint=(0.15, 0.06),
                                                                orientation='horizontal',
                                                                pos_hint={'x': 0.01, 'y': 0.01}))
                self.img.add_widget(self.transect)
                self.tMode = True
            else:
                # If button pressed while tools on screen, clears tools
                kivy.core.window.Window.set_system_cursor("arrow")
                self.img.remove_widget(self.transect)
                while len(self.ids.view.parent.children) > 1:
                    self.ids.view.parent.remove_widget(self.ids.view.parent.children[0])
                while len(self.img.children[0].children) > 1:
                    self.img.remove_widget(self.img.children[0].children[0])

                self.tMode = False

    def ncopen(self, dataset, file):
        # Creates image from nc file to display
        self.ds = dataset
        self.data = file[dataset].data
        ndata = (self.data - np.nanmin(self.data)) / (np.nanmax(self.data) - np.nanmin(self.data))
        ndata = np.nan_to_num(ndata, nan=1)

        # Applies colormap
        ndata = (ndata * 255).astype(np.uint8)
        ndata = np.array(list(map(lambda n: list(map(lambda r: _viridis_data[r], n)), ndata)))
        ndata = (ndata * 255).astype(np.uint8)
        img = im.fromarray(ndata)
        img.save("nc.jpg")

        self.img = ImageView(source=str("nc.jpg"), size=im.open("nc.jpg").size)
        self.ids.view.add_widget(self.img)
        self.img.addImage()
        self.fileon = True
        os.remove("nc.jpg")

    def gobtn(self):
        # Opens file and creates the interactive image
        if self.fileon:
            self.img.parent.remove_widget(self.img)
            self.fileon = False
            self.img = 0
            self.nc = False

        if self.tMode:
            # Cleans space for new image
            self.transect = SingleTransect(buttons=True, nc=False)
            kivy.core.window.Window.set_system_cursor("arrow")
            while len(self.ids.view.parent.children) > 1:
                self.ids.view.parent.remove_widget(self.ids.view.parent.children[0])
            self.tMode = False

        self.file = self.ids.file_in.text

        if len(self.file) >= 1:
            try:
                if self.file[-3:] == ".nc":
                    # Creates selection popup for nc file data sets
                    self.nc = True
                    ds = xr.open_dataset(self.file)
                    content = GridLayout(cols=3)
                    popup = Popup(title="Select Data Set", content=content, size_hint=(0.6, 0.6))
                    for i in list(ds.keys()):
                        btn = Button(text=i)
                        btn.bind(on_release=lambda btn: self.ncopen(btn.text, ds))
                        btn.bind(on_press=popup.dismiss)
                        content.add_widget(btn)
                    popup.open()
                # tiff files are not fully supported yet

                # elif self.file[-4:] == ".tif" or self.file[-5:] == ".tiff":
                #     # Creates interactive image from .tif/.tiff files
                #     image = im.open(self.file)
                #     imeg = np.asarray(image)
                #     a = np.histogram(imeg)
                #     print(a)
                #
                #     imeg = imeg - np.median(imeg) / (np.quantile(imeg, 0.75) - np.quantile(imeg, 0.25))
                #     imeg = (imeg - np.nanmin(imeg)) / (np.nanmax(imeg) - np.nanmin(imeg))
                #     a = np.histogram(imeg)
                #     print(a)
                #     imar = (imeg*255).astype(np.uint8)
                #     imar = np.reshape(imar, np.shape(imar)[-2:])
                #     out = im.fromarray(imar)
                #
                #     out.save("___.jpg")
                #     self.img = ImageView(source=str("___.jpg"), size=im.open("___.jpg").size)
                #     self.ids.view.add_widget(self.img)
                #     self.img.addImage()
                #     self.fileon = True
                #     os.remove("___.jpg")
                elif self.file[-5:] == ".jpeg" or self.file[-4:] == ".png" or self.file[-4:] == ".jpg":
                    # Creates interactive image from .jpg/.png/.jpeg files
                    self.img = ImageView(source=str(self.file), size=im.open(self.file).size)
                    self.ids.view.add_widget(self.img)
                    self.img.addImage()
                    self.fileon = True
                else:
                    alert("Unsupported File Type")

            except FileNotFoundError:
                alert("File Not Found")

    def rotate(self):
        # Rotate image
        if self.fileon:
            self.img.rotation = self.img.rotation + 45

    def quitbtn(self):
        # Quit application
        App.get_running_app().stop()


class FileGrab(ui.boxlayout.BoxLayout):
    pass


class MarkerWidth(ui.boxlayout.BoxLayout):
    # Marker width adjustment widget
    def __init__(self, marker, **kwargs):
        super(MarkerWidth, self).__init__(**kwargs)

        self.txt = TextInput(hint_text="Width", size_hint=(.7, 1))
        self.btn = RoundedButton(text="Go", size_hint=(.3, 1))
        self.btn.bind(on_press=lambda x: self.update())
        self.add_widget(self.txt)
        self.add_widget(self.btn)
        self.marker = marker
        self.spacing = 5

    def update(self):
        # Update width when button pressed
        num = self.txt.text
        if num.isnumeric():
            num = int(num)
            if 1 <= num <= 400:
                self.marker.update_width(num)

class MultiTransect(ui.widget.Widget):
    # Code for Multiple Transect tool, as well as base code for managing multiple single transects
    def __init__(self, **kwargs):
        super(MultiTransect, self).__init__(**kwargs)
        self.lines = []
        self.clicks = 0
        self.dbtn = Button()
        self.remove = True
        self.mpoints = 0

    def marker_points(self, plist):
        self.mpoints = plist

    def popup(self):
        # Gathers input and calls for popup
        if self.mpoints == 0:
            dfs = pd.DataFrame()
        else:
            dfs = pd.DataFrame(self.mpoints, columns=['Click X', 'Click Y'])

        count = 1
        for i in self.lines:
            # Gets transects from each single transect and loads into dataframe
            df = i.ipGetPoints()
            df.rename(columns={'x': 'x' + str(count), 'y': 'y' + str(count), 'Cut': 'Cut ' + str(count)},
                      inplace=True)
            dfs = pd.concat([dfs, df], axis=1)
            count += 1

        # Uses popup code from single_transect
        self.lines[0].plot_popup(dfs)

        # Clean up
        root.get_screen("HomeScreen").ids.view.parent.remove_widget(self.dbtn)
        if self.remove:
            self.parent.remove_widget(self.parent.children[0])

    def on_touch_down(self, touch):
        # Transect creation and display code

        # Determines what to do based on which of 3 click stages the user is in
        self.clicks += 1

        if self.clicks == 3:
            # Clean up download button from previous cycle
            self.clicks = 1
            root.get_screen("HomeScreen").ids.view.parent.remove_widget(self.dbtn)

        if self.clicks == 1:
            # Begins a new transect
            x = SingleTransect(buttons=False, nc=root.get_screen("HomeScreen").nc)

            self.add_widget(x)
            self.lines.append(x)

        # Single transect manages the line and dots graphics
        self.lines[-1].on_touch_down(touch)
        if self.clicks == 2:
            # Finishes a transect, displays download button
            self.dbtn = RoundedButton(text="Download", pos_hint={'x': .85, 'y': 0.02}, size=(dp(100), dp(30)),
                               size_hint_x=None, size_hint_y=None)
            root.get_screen("HomeScreen").ids.view.parent.add_widget(self.dbtn)
            self.dbtn.bind(on_press=lambda x: self.popup())


class SingleTransect(ui.widget.Widget):
    # Code for single transect widget, but also the base code for tools that do multiple transects
    def __init__(self, buttons, nc, **kwargs):
        super(SingleTransect, self).__init__(**kwargs)
        self.btns = buttons
        self.line = Line()
        self.circles = 0
        if platform.system() == "Darwin":
            self.line_width = dp(1)
            self.c_size = (dp(5), dp(5))
        else:
            self.line_width = dp(2)
            self.c_size = (dp(10), dp(10))
        self.btn = Button()
        self.nc = nc
        self.plot = 0

    def ipGetPoints(self):
        # Creates a data frame containing x, y, and value of points on transect line
        # If angle of line is > 45 degrees will swap x and y to still get an accurate answer
        r = 0
        data = []
        xyswap = False

        # Gather data as array
        if self.nc:
            img = root.get_screen("HomeScreen").data
        else:
            img = im.open(root.get_screen("HomeScreen").file).convert('RGB')

        line = self.line.points

        # Always read from left point to right
        if line[0] > line[2]:
            line = [line[2], line[3], line[0], line[1]]

        # Get interpolation object

        # Get x values
        ix = np.arange(int(line[0] - 3), int(line[2] + 4))

        # Get y values, if statement is to get y values increasing in value w/o changing og object

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
            m = 1 / m

        b = line[1] - m * (line[0])

        imgA = np.asarray(img)

        z = imgA[-(iy[-1] + 1):-(iy[0]), ix[0]:ix[-1] + 1]
        if not self.nc:
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
            df = pd.DataFrame({'x': yarr, 'y': xarr, 'Cut': data})
        else:
            df = pd.DataFrame({'x': xarr, 'y': yarr, 'Cut': data})

        return df

    def file_input(self, df, type):
        # Popup window for input of name for plot/csv file

        content = ui.boxlayout.BoxLayout(orientation='horizontal')
        popup = Popup(title="File Name", content=content, size_hint=(0.5, 0.15))
        txt = TextInput(size_hint=(0.7, 1), hint_text="Enter File Name")
        content.add_widget(txt)
        go = Button(text="Ok", size_hint=(0.3, 1))
        if type == "data":
            go.bind(on_press=lambda x: self.download_data(df, txt.text))
        else:
            go.bind(on_press=lambda x: self.download_plot(df, txt.text))
        go.bind(on_release=popup.dismiss)
        content.add_widget(go)
        popup.open()

    def download_plot(self, df, fname):
        # Code to make and download plot of a single transect
        plotdf(df, self.nc)

        if fname.find(".") >= 1:
            fname = fname[:fname.find(".")]

        # If file already exists, add (n) for n files
        exist = True
        fcount = 0
        while exist:
            if exists(fname + ".jpg"):
                fcount += 1
                if fcount == 1:
                    fname = fname + "(1)"
                else:
                    fname = fname[:fname.find("(")+1] + str(fcount) + ")"
            else:
                exist = False

        os.rename("____.jpg", fname + '.jpg')

        alert("Download Complete")

    def download_data(self, df, fname):
        # Downloads data into a csv file
        if fname.find(".") >= 1:
            fname = fname[:fname.find(".")]

        exist = True
        fcount = 0
        while exist:
            if exists(fname + ".csv"):
                fcount += 1
                if fcount == 1:
                    fname = fname + "(1)"
                else:
                    fname = fname[:fname.find("(")+1] + str(fcount) + ")"
            else:
                exist = False

        df.to_csv(fname + '.csv', index=False)
        alert("Download Complete")

    def plot_popup(self, df):
        # Opens popup window with plot and download options

        content = ui.boxlayout.BoxLayout(orientation='vertical', spacing=10)
        plotdf(df, self.nc)
        popup = Popup(title="Transect", content=content, size_hint=(0.8, 0.8))
        self.plot = ui.image.Image(source='____.jpg', size_hint=(1, .9))
        self.plot.reload()
        content.add_widget(self.plot)
        os.remove("____.jpg")

        btns = ui.boxlayout.BoxLayout(orientation='horizontal', size_hint=(1, .1), spacing = 5)

        dbtn = RoundedButton(text="Download to CSV", size_hint=(.5, 1))
        dbtn.bind(on_press=lambda x: self.file_input(df, 'data'))

        ibtn = RoundedButton(text='Download Plot', size_hint=(.5, 1))
        ibtn.bind(on_press=lambda x: self.file_input(df, 'plot'))

        btns.add_widget(dbtn)
        btns.add_widget(ibtn)
        content.add_widget(btns)

        self.line.points = []
        root.get_screen("HomeScreen").tMode = False
        kivy.core.window.Window.set_system_cursor("arrow")
        popup.open()

    def on_touch_down(self, touch):
        # Gathering touch coordinates and display line graphics
        if (self.circles < 1):
            self.circles += 1

            with self.canvas:
                Color(.28, .62, .86)
                self.line = Line(points=[], width=self.line_width)
                c1 = Ellipse(pos=(touch.x - self.c_size[0] / 2, touch.y - self.c_size[1] / 2), size=self.c_size)
                self.line.points = (touch.x, touch.y)

        elif (self.circles < 2):
            self.circles += 1

            with self.canvas:
                c2 = Ellipse(pos=(touch.x - self.c_size[0] / 2, touch.y - self.c_size[1] / 2), size=self.c_size)
                self.line.points += (touch.x, touch.y)

            if self.btns:
                # For when just a single transect, doesn't do buttons if just a base for a higher tool
                df = self.ipGetPoints()
                self.plot_popup(df)
                while len(self.parent.children) > 2:
                    self.parent.remove_widget(self.parent.children[0])
                self.parent.remove_widget(self.parent.children[0])

# NOT USED
class Click:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class MultiMarker(ui.widget.Widget):
    # Creates, stores, and manages downloads for multiple markers
    def __init__(self, **kwargs):
        super(MultiMarker, self).__init__(**kwargs)
        self.m_on = False
        self.dbtn = Button()
        self.upbtn = RoundedButton(text="Upload Project", pos_hint={'x': .01, 'y': 0.08}, size=(dp(115), dp(30)),
                            size_hint_x=None, size_hint_y=None)
        self.upbtn.bind(on_press=lambda x: self.upload_pop())
        root.get_screen("HomeScreen").ids.view.parent.add_widget(self.upbtn)

    def upload_pop(self):
        # Popup asking for file
        content = ui.boxlayout.BoxLayout(orientation='horizontal')
        popup = Popup(title="File Name", content=content, size_hint=(0.5, 0.15))
        txt = TextInput(size_hint=(0.7, 1), hint_text="Enter File Name")
        content.add_widget(txt)
        go = Button(text="Ok", size_hint=(0.3, 1))

        go.bind(on_release= lambda x: self.check_file(txt.text, popup))
        content.add_widget(go)
        popup.open()

    def check_file(self, file, popup):

        if exists(file):
            popup.dismiss()
            self.upload_data(file)
        else:
            content = Label(text="File Not Found")
            popup2 = Popup(title="Error", content=content, size_hint=(0.5, 0.15))
            popup2.open()

    def upload_data(self, folder):
        #start = time.time()
        for file in os.listdir(folder):
            f = pd.read_csv(folder + "/" + file)
            marker = Marker(nc=root.get_screen("HomeScreen").nc, multi=True)
            clicks = tuple(zip(f["Click X"].dropna(), f["Click Y"].dropna()))

            self.add_widget(marker)
            for i in clicks:
                marker.on_touch_down(Click(i[0], i[1]))
        # end = time.time()
        # print(abs(start - end))
        self.marker_off()
        # load markers and their bases as children
        #      - marker points needs click points
        #      - marker base needs MultiTransect
        #      - base needs SingleTransect per transect
        #      - SingleTransect needs Line with points corresponding to transect
        # add number labels and make new markers continue off of this number

    def update_width(self, num):
        self.children[0].twidth = num

    def new_marker(self):
        # Removes old marker

        # If current line has no clicks, delete current line and prev line
        if self.children[0].clicks == 0:
            self.remove_widget(self.children[0])

        if len(self.children) != 0:
            self.remove_widget(self.children[0])
        self.new_line()

    def new_line(self):
        # Creates a new marker
        m = Marker(nc=root.get_screen("HomeScreen").nc, multi=True)
        self.add_widget(m)

    def marker_off(self):
        # Update whether there is currently a marker on the board
        self.m_on = False

    def download_data(self, fname):
        #start = time.time()
        # Create a folder and download each marker's transect data into csv files
        # If user gave file name with a "." file extension, remove and just use name given by user
        if fname.find(".") >= 1:
            fname = fname[:fname.find(".")]
        if fname == "":
            alert("Invalid File Name")
            return
        # If folder name already exists add (n) for n files
        exist = True
        fcount = 0
        while exist:
            if exists(fname):
                fcount += 1
                if fcount == 1:
                    fname = fname + "(1)"
                else:
                    fname = fname[:fname.find("(") + 1] + str(fcount) + ")"
            else:
                exist = False
        os.mkdir(fname)

        # Create csv files
        frames = []
        c = 1
        for i in reversed(self.children):
            # For each marker
            columns = [None] * (2 + (len(i.base.lines)) * 3)
            columns[0:2] = ['Click X', 'Click Y']
            for k in range(0, len(i.base.lines)):
                index = 2 + k * 3
                columns[index] = 'x' + str(k + 1)
                columns[index + 1] = 'y' + str(k + 1)
                columns[index + 2] = 'Cut ' + str(k + 1)

            data = dict.fromkeys(columns)
            data['Click X'], data['Click Y'] = map(list, zip(*i.points))

            count = 1
            for j in i.base.lines:
                # For each line in marker
                df = j.ipGetPoints()
                data['x' + str(count)] = df['x'].to_list()
                data['y' + str(count)] = df['y'].to_list()
                data['Cut ' + str(count)] = df['Cut'].to_list()

                count += 1
            dfs = pd.DataFrame(dict([ (k,pd.Series(v)) for k,v in data.items() ]))
            dfs.to_csv(fname + '/marker(' + str(c) + ').csv', index=False)
            c += 1
        alert("Download Complete")
        #end = time.time()
        #print(abs(start - end))

    def file_input(self):
        # Create popup to ask for name of folder

        content = ui.boxlayout.BoxLayout(orientation='horizontal')
        popup = Popup(title="File Name", content=content, size_hint=(0.5, 0.15))

        txt = TextInput(size_hint=(0.7, 1), hint_text="Enter File Name")
        content.add_widget(txt)

        go = Button(text="Ok", size_hint=(0.3, 1))
        go.bind(on_release=lambda x: self.download_data(txt.text))
        go.bind(on_press=popup.dismiss)

        content.add_widget(go)
        popup.open()

    def on_touch_down(self, touch):
        # If no current marker, create marker. Otherwise pass touch to current marker.
        if not self.m_on:
            self.new_line()
            self.m_on = True
        self.children[0].on_touch_down(touch)



class Marker(ui.widget.Widget):
    # Code for a single marker. Uses a MultiTransect as a base but calculates orthogonal transects
    # rather than using user input

    def __init__(self, nc, multi, **kwargs):
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
        self.nc = nc
        self.multi = multi
        self.base = 0

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
        loc = root.get_screen("HomeScreen").ids.view.parent
        loc.remove_widget(self.dbtn)
        loc.remove_widget(loc.children[0])
        self.parent.remove_widget(self.parent.children[0])

    def on_touch_down(self, touch):
        # Draws marker line and points
        par = root.get_screen("HomeScreen").img.children[0].children[-2]
        self.clicks += 1
        with self.canvas:
            # Always adds point when clicked
            Color(.28, .62, .86)
            d = Ellipse(pos=(touch.x - self.c_size[0] / 2, touch.y - self.c_size[1] / 2), size=self.c_size)
            self.points.append((touch.x, touch.y))
        if self.clicks != 1:
            # If 2nd or more click, create a line inbetween click points

            self.dbtn = RoundedButton(text="Download", pos_hint={'x': .85, 'y': 0.02}, size=(dp(100), dp(30)),
                               size_hint_x=None, size_hint_y=None)

            if self.multi:
                self.dbtn.bind(on_press=lambda x: par.file_input())
            else:
                self.dbtn.bind(on_press=lambda x: self.run())
            root.get_screen("HomeScreen").ids.view.parent.add_widget(self.dbtn)

            with self.canvas:
                line = Line(points=[self.points[-2], self.points[-1]], width=self.line_width)
            # Stores orthogonal line in a SingleTransect which gets stored in base MultiTransect
            x = SingleTransect(buttons=False, nc=self.nc)
            x.line = copy.copy(line)
            x.line.points = self.get_orthogonal(line)
            self.base.lines.append(x)
        else:
            # If new marker creates MultiTransect base and download button

            self.base = MultiTransect()
            self.base.remove = False

            if self.multi:
                # Handles the buttons for multiple marker tool

                # New Line Button
                self.nbtn = RoundedButton(text="New Line", pos_hint={'x': .85, 'y': 0.1}, size=(dp(100), dp(30)),
                            size_hint_x=None, size_hint_y=None)

                self.nbtn.bind(on_press=lambda x: par.marker_off())
                root.get_screen("HomeScreen").ids.view.parent.add_widget(self.nbtn)

                # Delete Button
                self.delete = RoundedButton(text="Delete", pos_hint={'x': .85, 'y': 0.18}, size=(dp(100), dp(30)),
                            size_hint_x=None, size_hint_y=None)
                self.delete.bind(on_press=lambda x: par.new_marker())
                root.get_screen("HomeScreen").ids.view.parent.add_widget(self.delete)

                # Adds marker number
                number = Label(text=str(len(par.children)), pos=(touch.x, touch.y), font_size=30)
                self.add_widget(number)



class ImageView(ScatterLayout):
    # Creates interactive image
    # Dragging is managed by ScatterLayout widget base
    def __init__(self, size, source, **kwargs):
        super(ImageView, self).__init__(**kwargs)
        self.source = source
        self.size = size
        self.pos = root.get_screen("HomeScreen").ids.view.pos
        self.img = ui.image.Image(source=self.source)
        self.img.reload()
        self.add_widget(self.img)

    gMode = False
    ScatterLayout.do_rotation = False
    ScatterLayout.do_scale = False

    def addImage(self):
        # Starts up image
        self.img = ui.image.Image(source=self.source,  size=self.size, pos=self.parent.pos,
                         allow_stretch=True)

        # Begin at max size where you can see entire image
        wsize = root.get_screen("HomeScreen").ids.view.size
        isize = self.bbox[1]
        if isize[0] >= wsize[0] or isize[1] >= wsize[1]:
            while self.bbox[1][0] >= wsize[0] or self.bbox[1][1] >= wsize[1]:
                mat = Matrix().scale(.9, .9, .9)
                self.apply_transform(mat)
        if isize[0] <= wsize[0] and isize[1] <= wsize[1]:
            while self.bbox[1][0] <= wsize[0] and self.bbox[1][1] <= wsize[1]:
                mat = Matrix().scale(1.1, 1.1, 1.1)
                self.apply_transform(mat)

        xco = wsize[0] / 2 - self.bbox[1][0] / 2
        self.pos = (xco, self.pos[1])

    def on_touch_down(self, touch):
        # Scroll to zoom
        if self.collide_point(*touch.pos):
            if touch.is_mouse_scrolling:
                if touch.button == 'scrolldown':
                    if self.scale < 10:
                        mat = Matrix().scale(1.1, 1.1, 1.1)
                        self.apply_transform(mat, anchor=touch.pos)
                elif touch.button == 'scrollup':
                    if self.scale > 0.1:
                        mat = Matrix().scale(.9, .9, .9)
                        self.apply_transform(mat, anchor=touch.pos)
            else:
                super(ImageView, self).on_touch_down(touch)


class cutview(App):
    # Starts app and initializes window based on OS
    #    - Needs to be tested on max
    def on_start(self):
        # Kivy has a mobile app emulator that needs to be turned off for computer app
        kivy.config.Config.set('input', 'mouse', 'mouse,disable_multitouch')
        win = kivy.core.window.Window
        if platform.system() == "Darwin":
            win.size = (dp(500), dp(300))
            win.minimum_width = dp(400)
            win.minimum_height = dp(225)
        else:
            win.size = (dp(1000), dp(600))
            win.minimum_width = dp(800)
            win.minimum_height = dp(550)

    def build(self):
        global root
        root = ui.screenmanager.ScreenManager()
        root.add_widget(HomeScreen(name="HomeScreen"))
        return root


if __name__ == "__main__":
    cutview().run()
