from kivy.config import Config
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.graphics import Color, Ellipse, Line
from kivy.graphics.transformation import Matrix
from kivy.uix.image import Image
from kivy.uix.stencilview import StencilView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from functools import partial
from kivy.metrics import dp
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
from os.path import exists


def removeAlert(alert, *largs):
    root.get_screen("HomeScreen").ids.view.parent.remove_widget(alert)


def plotdf(df, nc):
    ndf = pd.DataFrame()

    for i in df.columns:
        if i[0:3] == "Cut":
            ndf[i] = df[i]
    x = np.asarray(ndf.index)
    ndf.index = (x - x[0]) / (x[-1] - x[0])
    plt.plot(ndf)
    if nc:
        plt.ylabel("NC Value")
    else:
        plt.ylabel("Mean RGB Value")
        plt.gca().set_ylim(ymin=0)
    plt.xlabel("Normalized Long Transect Distance")
    plt.legend(ndf.columns, title="Legend", bbox_to_anchor=(1.05, 1))
    plt.tight_layout()
    plt.savefig("____.jpg")
    plt.close('all')


class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super(HomeScreen, self).__init__(**kwargs)
        self.fileon = False
        self.img = 0
        self.transect = SingleTransect(buttons=True, nc=False)
        self.tMode = False
        self.data = 0
        self.nc = False
        self.file = 0

    def transectbtn(self, type):
        if self.fileon:
            if not self.tMode:
                Window.set_system_cursor("crosshair")
                if type == "single":
                    self.transect = SingleTransect(buttons=True, nc=self.nc)
                elif type == "multi":
                    self.transect = MultiTransect()
                elif type == "filament":
                    self.transect = MultiMarker()
                    self.ids.view.parent.add_widget(MarkerWidth(self.transect,
                                                                size_hint=(0.15, 0.06),                                               orientation='horizontal'))
                else:
                    self.transect = Marker(nc=self.nc, multi=False)
                    self.ids.view.parent.add_widget(MarkerWidth(self.transect,
                                                                size_hint=(0.15, 0.06),
                                                                orientation='horizontal'))
                self.img.add_widget(self.transect)
                self.tMode = True
            else:
                Window.set_system_cursor("arrow")
                self.img.remove_widget(self.transect)
                while len(self.ids.view.parent.children) > 1:
                    self.ids.view.parent.remove_widget(self.ids.view.parent.children[0])
                while len(self.img.children[0].children) > 1:
                    self.img.remove_widget(self.img.children[0].children[0])

                self.tMode = False

    def ncopen(self, dataset, file):

        self.data = file[dataset].data
        ndata = (self.data - np.nanmin(self.data)) / (np.nanmax(self.data) - np.nanmin(self.data))
        ndata = np.nan_to_num(ndata, nan=1)
        img = im.fromarray((ndata * 255).astype(np.uint8))
        img.save("nc.jpg")
        self.img = ImageView(source=str("nc.jpg"), size=im.open("nc.jpg").size)
        self.ids.view.add_widget(self.img)
        self.img.addImage()
        self.fileon = True
        os.remove("nc.jpg")

    def gobtn(self):

        if self.fileon:
            self.img.parent.remove_widget(self.img)
            self.fileon = False
            self.img = 0
            self.nc = False

        if self.tMode:
            self.transect = SingleTransect(buttons=True, nc=False)
            Window.set_system_cursor("arrow")
            while len(self.ids.view.parent.children) > 1:
                self.ids.view.parent.remove_widget(self.ids.view.parent.children[0])
            self.tMode = False

        self.file = self.ids.file_in.text

        if len(self.file) >= 1:
            try:
                if self.file[-3:] == ".nc":
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
                else:
                    self.img = ImageView(source=str(self.file), size=im.open(self.file).size)
                    self.ids.view.add_widget(self.img)
                    self.img.addImage()
                    self.fileon = True

            except FileNotFoundError:
                alert = Label(text="File Not Found", size_hint=(0.2, 0.1), color=(0, 0, 0, 1))
                self.ids.view.parent.add_widget(alert)
                Clock.schedule_once(partial(removeAlert, alert), 2)

    def rotate(self):
        if self.fileon:
            self.img.rotation = self.img.rotation + 45

    def quitbtn(self):
        App.get_running_app().stop()


class ViewerWindow(StencilView):
    pass


class FileGrab(BoxLayout):
    pass


class MarkerWidth(BoxLayout):
    def __init__(self, marker, **kwargs):
        super(MarkerWidth, self).__init__(**kwargs)

        self.txt = TextInput(hint_text="Width", size_hint=(.7, 1))
        self.btn = Button(text="Go", size_hint=(.3, 1))
        self.btn.bind(on_press=lambda x: self.update())
        self.add_widget(self.txt)
        self.add_widget(self.btn)
        self.marker = marker

    def update(self):
        num = self.txt.text
        if num.isnumeric():
            num = int(num)
            if 1 <= num <= 400:
                self.marker.update_width(num)

class MultiTransect(Widget):

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

        if self.mpoints == 0:
            dfs = pd.DataFrame()
        else:
            dfs = pd.DataFrame(self.mpoints, columns=['Click X', 'Click Y'])

        count = 1
        for i in self.lines:
            df = i.ipGetPoints()
            df.rename(columns={'x': 'x' + str(count), 'y': 'y' + str(count), 'Cut': 'Cut ' + str(count)},
                      inplace=True)
            dfs = pd.concat([dfs, df], axis=1)
            count += 1

        self.lines[0].plot_popup(dfs)

        root.get_screen("HomeScreen").ids.view.parent.remove_widget(self.dbtn)
        if self.remove:
            self.parent.remove_widget(self.parent.children[0])

    def on_touch_down(self, touch):

        self.clicks += 1

        if self.clicks == 3:
            self.clicks = 1
            root.get_screen("HomeScreen").ids.view.parent.remove_widget(self.dbtn)

        if self.clicks == 1:
            x = SingleTransect(buttons=False, nc=root.get_screen("HomeScreen").nc)
            self.add_widget(x)
            self.lines.append(x)
        self.lines[-1].on_touch_down(touch)
        if self.clicks == 2:
            self.dbtn = Button(text="Download", pos_hint={'x': .85, 'y': 0.02}, size=(dp(100), dp(30)),
                               size_hint_x=None, size_hint_y=None)
            root.get_screen("HomeScreen").ids.view.parent.add_widget(self.dbtn)
            self.dbtn.bind(on_press=lambda x: self.popup())


class SingleTransect(Widget):

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
        r = 0
        data = []
        xyswap = False

        if self.nc:
            img = root.get_screen("HomeScreen").data
        else:
            img = im.open(root.get_screen("HomeScreen").file).convert('RGB')

        line = self.line.points

        # always read from left point to right
        if line[0] > line[2]:
            line = [line[2], line[3], line[0], line[1]]

        # get interpolation object

        # get x values
        ix = np.arange(int(line[0] - 3), int(line[2] + 4))

        # get y values, if is to get y values increasing in value w/o changing og object

        if line[1] > line[3]:
            iy = np.arange(int(line[3] - 3), int(line[1] + 4))
        else:
            iy = np.arange(int(line[1] - 3), int(line[3] + 4))

        # get the line

        if line[2] - line[0] == 0:
            m = (line[3] - line[1]) / .001
        else:
            m = (line[3] - line[1]) / (line[2] - line[0])

        # if slope greater than 45 deg swap xy

        if abs(math.atan(m)) > (math.pi / 4):
            # print("xyswap!")
            xyswap = True
            line = [line[1], line[0], line[3], line[2]]
            m = 1 / m

        b = line[1] - m * (line[0])

        imgA = np.asarray(img)

        z = imgA[-(iy[-1] + 1):-(iy[0]), ix[0]:ix[-1] + 1]
        if not self.nc:
            z = np.mean(z, axis=2)
        z = np.flipud(z)

        # numpy arrays are indexed by row, column NOT x, y, but interp object does do x y
        intPol = interpolate.interp2d(ix, iy, z, kind='linear')

        # avg around

        if line[0] > line[2]:
            xarr = np.arange(int(line[2]), int(line[0]))
        else:
            xarr = np.arange(int(line[0]), int(line[2]))

        yarr = xarr * m + b

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
        content = BoxLayout(orientation='horizontal')
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

        plotdf(df, self.nc)

        if fname.find(".") >= 1:
            fname = fname[:fname.find(".")]

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

        alert = Button(text="Download Complete", size_hint=(0.25, 0.1), disabled=True)
        root.get_screen("HomeScreen").ids.view.parent.add_widget(alert)
        Clock.schedule_once(partial(removeAlert, alert), 2)

    def download_data(self, df, fname):

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
        alert = Button(text="Download Complete", size_hint=(0.25, 0.1), disabled=True)
        root.get_screen("HomeScreen").ids.view.parent.add_widget(alert)
        Clock.schedule_once(partial(removeAlert, alert), 2)

    def plot_popup(self, df):

        content = BoxLayout(orientation='vertical')
        plotdf(df, self.nc)
        popup = Popup(title="Transect", content=content, size_hint=(0.8, 0.8))
        self.plot = Image(source='____.jpg', size_hint=(1, .9))
        self.plot.reload()
        content.add_widget(self.plot)
        os.remove("____.jpg")

        btns = BoxLayout(orientation='horizontal', size_hint=(1, .1))

        dbtn = Button(text="Download to CSV", size_hint=(.5, 1))
        dbtn.bind(on_press=lambda x: self.file_input(df, 'data'))

        ibtn = Button(text='Download Plot', size_hint=(.5, 1))
        ibtn.bind(on_press=lambda x: self.file_input(df, 'plot'))

        btns.add_widget(dbtn)
        btns.add_widget(ibtn)
        content.add_widget(btns)

        self.line.points = []
        root.get_screen("HomeScreen").tMode = False
        Window.set_system_cursor("arrow")
        popup.open()

    def on_touch_down(self, touch):
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
                df = self.ipGetPoints()
                self.plot_popup(df)
                while len(self.parent.children) > 2:
                    self.parent.remove_widget(self.parent.children[0])
                self.parent.remove_widget(self.parent.children[0])


class MultiMarker(Widget):
    def __init__(self, **kwargs):
        super(MultiMarker, self).__init__(**kwargs)
        self.m_on = False
        self.dbtn = Button()

    def update_width(self, num):
        self.children[0].twidth = num

    def new_marker(self):
        self.remove_widget(self.children[0])
        self.new_line()

    def new_line(self):
        m = Marker(nc=root.get_screen("HomeScreen").nc, multi=True)
        #root.get_screen("HomeScreen").img.add_widget
        self.add_widget(m)

    def flipmon(self):
        self.m_on = False

    def download_data(self, fname):
        if fname.find(".") >= 1:
            fname = fname[:fname.find(".")]

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

        c = 1
        for i in reversed(self.children):

            dfs = pd.DataFrame(i.points, columns=['Click X', 'Click Y'])
            count = 1
            for j in i.base.lines:
                df = j.ipGetPoints()
                df.rename(columns={'x': 'x' + str(count), 'y': 'y' + str(count), 'Cut': 'Cut ' + str(count)},
                          inplace=True)
                dfs = pd.concat([dfs, df], axis=1)
                count += 1
            print(dfs)
            dfs.to_csv(fname + '/marker(' + str(c) + ').csv', index=False)
            c += 1

    def file_input(self):
        content = BoxLayout(orientation='horizontal')
        popup = Popup(title="File Name", content=content, size_hint=(0.5, 0.15))

        txt = TextInput(size_hint=(0.7, 1), hint_text="Enter File Name")
        content.add_widget(txt)

        go = Button(text="Ok", size_hint=(0.3, 1))
        go.bind(on_press=lambda x: self.download_data(txt.text))
        go.bind(on_release=popup.dismiss)

        content.add_widget(go)
        popup.open()

    # NOT USED
    def run(self):
        print(self.children)
        content = BoxLayout(orientation='vertical')
        popup = Popup(title="Download Markers", content=content, size_hint=(0.8, 0.8))
        btns = BoxLayout(orientation='horizontal', size_hint=(1, .1))

        dbtn = Button(text="Download to CSV", size_hint=(.5, 1))
        dbtn.bind(on_press=lambda x: self.file_input())
        btns.add_widget(dbtn)
        content.add_widget(btns)

        popup.open()
        print("ur done")

    def on_touch_down(self, touch):
        if not self.m_on:
            self.new_line()
            self.m_on = True
        self.children[0].on_touch_down(touch)



class Marker(Widget):

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
        self.twidth = width

    def get_orthogonal(self, line):

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
            # print("xyswap!")
            xyswap = True
            line = [line[1], line[0], line[3], line[2]]
            m = 1 / m

        mid = (line[0] + (line[2] - line[0]) / 2, line[1] + (line[3] - line[1]) / 2)

        b = mid[1] - m * mid[0]
        xarr = np.arange(int(mid[0] - self.twidth / 2), int(mid[0] + self.twidth / 2))
        yarr = xarr * m + b

        with self.canvas:
            Color(.28, .62, .86)
            coords = [xarr[0], yarr[0], xarr[-1], yarr[-1]]
            if xyswap:
                coords = [yarr[0], xarr[0], yarr[-1], xarr[-1]]
            c1 = Ellipse(pos=(coords[0] - self.c_size[0] / 2, coords[1] - self.c_size[1] / 2), size=self.c_size)
            c1 = Ellipse(pos=(coords[2] - self.c_size[0] / 2, coords[3] - self.c_size[1] / 2), size=self.c_size)
        return coords

    def run(self):
        self.base.marker_points(self.points)
        self.base.popup()
        loc = root.get_screen("HomeScreen").ids.view.parent
        loc.remove_widget(self.dbtn)
        loc.remove_widget(loc.children[0])
        self.parent.remove_widget(self.parent.children[0])

    def on_touch_down(self, touch):

        self.clicks += 1
        with self.canvas:
            Color(.28, .62, .86)
            d = Ellipse(pos=(touch.x - self.c_size[0] / 2, touch.y - self.c_size[1] / 2), size=self.c_size)
            self.points.append((touch.x, touch.y))
        if self.clicks != 1:
            with self.canvas:
                line = Line(points=[self.points[-2], self.points[-1]], width=self.line_width)
            x = SingleTransect(buttons=False, nc=self.nc)
            x.line = copy.copy(line)
            x.line.points = self.get_orthogonal(line)
            self.base.lines.append(x)
        else:
            self.base = MultiTransect()
            self.base.remove = False
            self.dbtn = Button(text="Download", pos_hint={'x': .85, 'y': 0.02}, size=(dp(100), dp(30)),
                               size_hint_x=None, size_hint_y=None)
            if self.multi:
                self.nbtn = Button(text="New Line", pos_hint={'x': .85, 'y': 0.1}, size=(dp(100), dp(30)),
                            size_hint_x=None, size_hint_y=None)
                par = root.get_screen("HomeScreen").img.children[0].children[-2]
                self.nbtn.bind(on_press=lambda x: par.flipmon())
                root.get_screen("HomeScreen").ids.view.parent.add_widget(self.nbtn)
                self.dbtn.bind(on_press=lambda x: par.file_input())

                self.delete = Button(text="Delete", pos_hint={'x': .85, 'y': 0.18}, size=(dp(100), dp(30)),
                            size_hint_x=None, size_hint_y=None)
                self.delete.bind(on_press=lambda x: par.new_marker())
                root.get_screen("HomeScreen").ids.view.parent.add_widget(self.delete)
                number = Label(text=str(len(par.children)), pos=(touch.x, touch.y), font_size=30)
                self.add_widget(number)


            else:
                self.dbtn.bind(on_press=lambda x: self.run())
            root.get_screen("HomeScreen").ids.view.parent.add_widget(self.dbtn)


class ImageView(ScatterLayout):

    def __init__(self, size, source, **kwargs):
        super(ImageView, self).__init__(**kwargs)
        self.source = source
        self.size = size
        self.pos = root.get_screen("HomeScreen").ids.view.pos
        self.img = Image(source=self.source)
        self.img.reload()
        self.add_widget(self.img)

    gMode = False
    ScatterLayout.do_rotation = False
    ScatterLayout.do_scale = False

    def addImage(self):
        self.img = Image(source=self.source,  size=self.size, pos=self.parent.pos,
                         allow_stretch=True)

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

    def on_start(self):
        Config.set('input', 'mouse', 'mouse,disable_multitouch')
        if platform.system() == "Darwin":
            Window.size = (dp(500), dp(300))
            Window.minimum_width = dp(400)
            Window.minimum_height = dp(225)
        else:
            Window.size = (dp(1000), dp(600))
            Window.minimum_width = dp(800)
            Window.minimum_height = dp(550)

    def build(self):
        global root
        root = ScreenManager()
        root.add_widget(HomeScreen(name="HomeScreen"))
        return root


if __name__ == "__main__":
    cutview().run()
