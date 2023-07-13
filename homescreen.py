import kivy
from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.button import Button
import numpy as np
import xarray as xr
import os
import re
from PIL import Image as im
import functions as func
from singletransect import SingleTransect
from multitransect import MultiTransect
from markerwidth import MarkerWidth
from multimarker import MultiMarker
from imageview import ImageView
from marker import Marker
from cmaps import _viridis_data


class HomeScreen(Screen):
    # Main screen functionality
    def __init__(self, **kwargs):
        super(HomeScreen, self).__init__(**kwargs)
        self.fileon = False
        self.img = 0
        self.transect = SingleTransect(buttons=True, home=self)
        self.tMode = False
        self.data = 0
        self.ds = 0
        self.nc = False
        self.file = 0
        self.rgb = 0

    def transectbtn(self, type):
        # Manages the creation and deletion of each tool
        if self.fileon:
            if not self.tMode:
                # Opens a new tool
                kivy.core.window.Window.set_system_cursor("crosshair")
                if type == "single":
                    self.transect = SingleTransect(buttons=True, home=self)
                elif type == "multi":
                    self.transect = MultiTransect(home=self)
                elif type == "filament":
                    self.transect = MultiMarker(home=self)
                else:
                    self.transect = Marker(multi=False, home=self)
                    self.ids.view.parent.add_widget(MarkerWidth(self.transect,
                                                                size_hint=(0.15, 0.06),
                                                                orientation='horizontal',
                                                                pos_hint={'x': 0.01, 'y': 0.01}))
                self.img.add_widget(self.transect)
                self.tMode = True
            else:
                # If button pressed while tools on screen, clears tools and all buttons
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

        self.img = ImageView(source=str("nc.jpg"), size=im.open("nc.jpg").size, home=self)
        self.ids.view.add_widget(self.img)
        self.img.addImage()
        self.fileon = True
        os.remove("nc.jpg")

    def gobtn(self):

        # Opens file and creates the interactive image
        if self.fileon:
            # If file open, clear previous file data
            self.img.parent.remove_widget(self.img)
            self.fileon = False
            self.img = 0
            self.rgb = 0
            self.nc = False

        if self.tMode:
            # Cleans space for new image
            self.transect = SingleTransect(buttons=True, home=self)
            kivy.core.window.Window.set_system_cursor("arrow")
            while len(self.ids.view.parent.children) > 1:
                self.ids.view.parent.remove_widget(self.ids.view.parent.children[0])
            self.tMode = False

        self.file = self.ids.file_in.text
        # Limit file names to alphanumeric characters and _-./
        if self.file == "" or len(re.findall(r'[^A-Za-z0-9_.\-/]', self.file)) > 0:
            func.alert("Invalid File Name", self)
        else:
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

                    elif self.file[-5:] == ".jpeg" or self.file[-4:] == ".png" or self.file[-4:] == ".jpg":
                        # Creates interactive image from .jpg/.png/.jpeg files
                        self.img = ImageView(source=str(self.file), size=im.open(self.file).size, home=self)
                        self.ids.view.add_widget(self.img)
                        self.img.addImage()
                        self.rgb = im.open(self.file).convert('RGB')
                        self.fileon = True
                    else:
                        func.alert("Unsupported File Type", self)

                except FileNotFoundError:
                    func.alert("File Not Found", self)

    def rotate(self):
        # Rotate image
        if self.fileon:
            self.img.rotation = self.img.rotation + 45

    def canvas_remove(self, item, *largs):
        # Allows external sources to clear canvas
        self.canvas.remove(item)

    def quitbtn(self):
        # Quit application
        App.get_running_app().stop()
