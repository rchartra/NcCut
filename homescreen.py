"""
Functionality for main app screen
"""

import kivy
from kivy.app import App
from kivy.uix.screenmanager import Screen
import re
import functions as func
from pathlib import Path
from multitransect import MultiTransect
from multimarker import MultiMarker
from imageview import ImageView
from netcdfconfig import NetCDFConfig
from PIL import Image as im
import cv2


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
        self.cmaps = {"Autumn": cv2.COLORMAP_AUTUMN, "Bone": cv2.COLORMAP_BONE, "Jet": cv2.COLORMAP_JET,
                      "Winter": cv2.COLORMAP_WINTER, "Rainbow": cv2.COLORMAP_RAINBOW, "Ocean": cv2.COLORMAP_OCEAN,
                      "Summer": cv2.COLORMAP_SUMMER, "Spring": cv2.COLORMAP_SPRING, "Cool": cv2.COLORMAP_COOL,
                      "HSV": cv2.COLORMAP_HSV, "Pink": cv2.COLORMAP_PINK, "Hot": cv2.COLORMAP_HOT,
                      "Parula": cv2.COLORMAP_PARULA, "Magma": cv2.COLORMAP_MAGMA, "Inferno": cv2.COLORMAP_INFERNO,
                      "Plasma": cv2.COLORMAP_PLASMA, "Viridis": cv2.COLORMAP_VIRIDIS, "Cividis": cv2.COLORMAP_CIVIDIS,
                      "Twilight": cv2.COLORMAP_TWILIGHT, "Twilight Shifted": cv2.COLORMAP_TWILIGHT_SHIFTED,
                      "Turbo": cv2.COLORMAP_TURBO, "Deep Green": cv2.COLORMAP_DEEPGREEN}
        self.colormap = 'Viridis'
        self.nc = False
        self.img = ImageView(home=self)
        self.action = func.BackgroundLabel(text="Actions", size_hint=(1, 0.1), text_size=self.size,
                                           halign='center', valign='center', font_size=self.size[0] / 8)
        self.drag = func.RoundedButton(text="Drag Mode", size_hint=(1, 0.1), text_size=self.size,
                                       halign='center', valign='center', font_size=self.size[0] / 8)
        self.edit = func.RoundedButton(text="Edit Mode", size_hint=(1, 0.1), text_size=self.size,
                                       halign='center', valign='center', font_size=self.size[0] / 8)
        self.netcdf = {}
        self.data = 0
        self.transect = 0
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
                self.netcdf['var'] = value
                self.data = self.sel_data(self.netcdf)
                self.img.update_netcdf(self.data)
        elif setting == "depth":
            if self.fileon and self.nc and self.netcdf['z'] != 'Select...':
                self.netcdf['z_val'] = value
                self.data = self.sel_data(self.netcdf)
                self.img.update_netcdf(self.data)
        elif setting == "l_color":
            self.l_col = value
        elif setting == "cir_size":
            self.cir_size = float(value)
        elif setting == "output":
            self.rel_path = Path(value)

    def update_color_bar(self, colorbar):
        # Takes colorbar widget and adds it to menu bar
        if len(self.ids.colorbar.children) != 0:
            self.ids.colorbar.remove_widget(self.ids.colorbar.children[0])
        self.ids.colorbar.add_widget(colorbar)

    def transect_btn(self, type):
        # Manages the creation and deletion of each tool
        if self.fileon:
            if not self.tMode:
                # Opens a new tool
                self.ids.sidebar.add_widget(self.action, 1)
                self.drag.bind(on_press=self.img.drag_mode)
                self.edit.bind(on_press=self.img.edit_mode)
                self.ids.sidebar.add_widget(self.drag, 1)
                self.ids.sidebar.add_widget(self.edit, 1)
                kivy.core.window.Window.set_system_cursor("crosshair")
                if type == "transect":
                    self.transect = MultiTransect(home=self)
                elif type == "transect_marker":
                    self.transect = MultiMarker(home=self)
                self.img.add_widget(self.transect)
                self.tMode = True
            else:
                # If button pressed while tools on screen, clears tools and all new sidebar buttons
                kivy.core.window.Window.set_system_cursor("arrow")
                self.img.remove_widget(self.transect)
                self.drag.text = "Drag Mode"
                self.img.editing = False
                while len(self.ids.sidebar.children) > 4:
                    self.ids.sidebar.remove_widget(self.ids.sidebar.children[1])
                self.tMode = False

    def nc_open(self, config):
        # Creates image from nc file to display
        self.netcdf = config
        self.data = self.sel_data(config)
        self.img.load_file(source=self.data, f_type="netcdf")
        self.fileon = True
        self.nc = True

    def sel_data(self, config):
        # Selects data based on user dimension and variable selections
        if config['z'] == 'Select...':
            # 2D NetCDF data
            ds = config['file'][config['var']].rename({config['y']: 'y', config['x']: 'x'})
            ds = ds.transpose('x', 'y')
            data = ds.sel(x=ds['x'], y=ds['y'])
            data = data.data
        else:
            # 3D NetCDF data
            ds = config['file'][config['var']].rename({config['y']: 'y', config['x']: 'x', config['z']: 'z'})
            ds = ds.transpose('x', 'y', 'z')
            ds['z'] = ds['z'].astype(str)
            data = ds.sel(x=ds['x'], y=ds['y'], z=config['z_val'])
            data = data.data
        return data

    def gobtn(self):
        # Opens file and creates the interactive image
        if self.fileon:
            # If file open, clear previous file data
            self.clean_file()

        if self.tMode:
            # Cleans space for new image
            self.transect = 0
            kivy.core.window.Window.set_system_cursor("arrow")
            while len(self.ids.view.parent.children) > 1:
                self.ids.view.parent.remove_widget(self.ids.view.parent.children[0])
            while len(self.ids.sidebar.children) > 4:
                self.ids.sidebar.remove_widget(self.ids.sidebar.children[1])
            self.tMode = False
        self.ids.view.add_widget(self.img)
        self.file = self.ids.file_in.text
        # Limit file names to alphanumeric characters and _-./
        if self.file == "" or len(re.findall(r'[^A-Za-z0-9_.\-/]', self.file)) > 0:
            func.alert("Invalid File Name", self)
            self.clean_file()
        else:
            if len(self.file) >= 1:
                try:
                    open(self.file)
                    if self.file[-3:] == ".nc":
                        # Creates selection popup for nc file data sets
                        NetCDFConfig(self.file, self)

                    elif self.file[-5:] == ".jpeg" or self.file[-4:] == ".png" or self.file[-4:] == ".jpg":
                        # Creates interactive image from .jpg/.png/.jpeg files
                        self.img.load_file(source=str(self.file), f_type="image")
                        self.rgb = im.open(self.file).convert('RGB')
                        self.fileon = True
                    else:
                        func.alert("Unsupported File Type", self)
                        self.clean_file()

                except FileNotFoundError:
                    func.alert("File Not Found", self)
                    self.clean_file()

    def clean_file(self):
        # Resets file related attributes
        if len(self.ids.colorbar.children) != 0:
            self.ids.colorbar.remove_widget(self.ids.colorbar.children[0])
        self.img.parent.remove_widget(self.img)
        self.fileon = False
        self.img = ImageView(home=self)
        self.rgb = 0
        self.nc = False

    def canvas_remove(self, item, *largs):
        # Allows external sources to clear canvas
        self.canvas.remove(item)

    def quit_btn(self):
        # Quit application
        App.get_running_app().stop()
