import kivy
from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.metrics import dp
import xarray as xr
import re
import functions as func
from pathlib import Path
from multitransect import MultiTransect
from multimarker import MultiMarker
from imageview import ImageView
from PIL import Image as im


class HomeScreen(Screen):
    # Main screen functionality
    def __init__(self, **kwargs):
        super(HomeScreen, self).__init__(**kwargs)
        self.fileon = False
        self.tMode = False
        self.rel_path = Path(App.get_running_app().config.get('main', 'output'))
        self.l_col = "Blue"
        self.cir_size = 10
        self.contrast = 1.0
        self.colormap = 'viridis'
        self.nc = False
        self.action = func.BackgroundLabel(text="Actions", size_hint=(1, 0.1), text_size=self.size,
                                           halign='center', valign='center', font_size=self.size[0] / 8)
        self.transect = 0
        self.data = 0
        self.ds = 0
        self.img = 0
        self.file = 0
        self.rgb = 0

    def update_settings(self, setting, value):
        # Updates app settings depending on context of setting change

        if setting == "contrast":
            if self.fileon and self.nc:
                self.contrast = value
                self.img.update_contrast(float(value))
        elif setting == "colormap":
            if self.fileon and self.nc:
                self.colormap = value
                self.img.update_colormap(value)
        elif setting == "variable":
            if self.fileon and self.nc:
                self.ds = value
                self.data = xr.open_dataset(self.file)[value].data
                self.img.update_variable(self.data)
        elif setting == "l_color":
            self.l_col = value
        elif setting == "cir_size":
            self.cir_size = float(value)
        elif setting == "output":
            self.rel_path = Path(value)

    def transectbtn(self, type):
        # Manages the creation and deletion of each tool
        if self.fileon:
            if not self.tMode:
                # Opens a new tool
                self.ids.sidebar.add_widget(self.action, 1)
                kivy.core.window.Window.set_system_cursor("crosshair")
                if type == "transect":
                    self.transect = MultiTransect(home=self)
                elif type == "transect_marker":
                    self.transect = MultiMarker(home=self)
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
                while len(self.ids.sidebar.children) > 4:
                    self.ids.sidebar.remove_widget(self.ids.sidebar.children[1])
                self.tMode = False

    def ncopen(self, dataset, file):
        # Creates image from nc file to display
        self.ds = dataset
        self.data = file[dataset].data

        self.img = ImageView(source=self.data, home=self, f_type="netcdf")
        self.ids.view.add_widget(self.img)
        self.img.addImage()
        self.fileon = True

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
            self.transect = 0
            kivy.core.window.Window.set_system_cursor("arrow")
            while len(self.ids.view.parent.children) > 1:
                self.ids.view.parent.remove_widget(self.ids.view.parent.children[0])
            while len(self.ids.sidebar.children) > 4:
                self.ids.sidebar.remove_widget(self.ids.sidebar.children[1])
            self.tMode = False

        self.file = self.ids.file_in.text
        # Limit file names to alphanumeric characters and _-./
        if self.file == "" or len(re.findall(r'[^A-Za-z0-9_.\-/]', self.file)) > 0:
            func.alert("Invalid File Name", self)
        else:
            if len(self.file) >= 1:
                try:
                    open(self.file)
                    if self.file[-3:] == ".nc":
                        # Creates selection popup for nc file data sets
                        self.nc = True
                        ds = xr.open_dataset(self.file)
                        content = BoxLayout(orientation='vertical', spacing=dp(10))
                        grid = GridLayout(cols=3, size_hint=(1, 0.9))
                        popup = Popup(title="Select Data Set", content=content, size_hint=(0.6, 0.6))
                        for i in list(ds.keys()):
                            btn = Button(text=i)
                            btn.bind(on_release=lambda btn: self.ncopen(btn.text, ds))
                            btn.bind(on_press=popup.dismiss)
                            grid.add_widget(btn)
                        content.add_widget(grid)
                        close = Button(text="Close", size_hint=(0.2, 0.1), font_size=self.size[0] / 60)
                        close.bind(on_press=popup.dismiss)
                        content.add_widget(close)
                        popup.open()

                    elif self.file[-5:] == ".jpeg" or self.file[-4:] == ".png" or self.file[-4:] == ".jpg":
                        # Creates interactive image from .jpg/.png/.jpeg files
                        self.img = ImageView(source=str(self.file), home=self, f_type="image")
                        self.ids.view.add_widget(self.img)
                        self.img.addImage()
                        self.rgb = im.open(self.file).convert('RGB')
                        self.fileon = True
                    else:
                        func.alert("Unsupported File Type", self)

                except FileNotFoundError:
                    func.alert("File Not Found", self)

    def canvas_remove(self, item, *largs):
        # Allows external sources to clear canvas
        self.canvas.remove(item)

    def quitbtn(self):
        # Quit application
        App.get_running_app().stop()
