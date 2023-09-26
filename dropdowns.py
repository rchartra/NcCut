from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.app import App
import cv2
import cmaps
import xarray as xr


class ViewDropDown(DropDown):
    def __init__(self, **kwargs):
        super(ViewDropDown, self).__init__(**kwargs)
        self.home = App.get_running_app().root.get_screen("HomeScreen")

        col_list = ["Blue", "Orange", "Green"]
        self.l_color_drop = DropDown()
        for i in col_list:
            btn = Button(text=i, size_hint_y=None, height=30)
            btn.bind(on_release=lambda btn: self.pass_setting("l_color", btn.text))
            btn.bind(on_press=self.l_color_drop.dismiss)
            self.l_color_drop.add_widget(btn)

    def pass_setting(self, setting, value):
        self.home.update_settings(setting, value)

    def rotate(self):
        # Rotate image
        if self.home.fileon:
            self.home.img.rotation = self.home.img.rotation + 45

    def flip_v(self):
        if self.home.fileon:
            self.home.img.flip_vertically()

    def flip_h(self):
        if self.home.fileon:
            self.home.img.flip_horizontally()


class NetCDFDropDown(DropDown):
    def __init__(self, **kwargs):
        super(NetCDFDropDown, self).__init__(**kwargs)
        self.home = App.get_running_app().root.get_screen("HomeScreen")

        # Colormap dropdown from maps listed in cmaps.py
        self.cmap_dropdown = DropDown()
        for i in list(self.home.cmaps.keys()):
            btn = Button(text=i, size_hint_y=None, height=30)
            btn.bind(on_release=lambda btn: self.pass_setting("colormap", btn.text))
            btn.bind(on_press=self.cmap_dropdown.dismiss)
            self.cmap_dropdown.add_widget(btn)

        # Dropdown of Variables in Dataset
        self.var_dropdown = DropDown()
        if isinstance(self.home.file, str) and self.home.nc:
            for i in list(xr.open_dataset(self.home.file).keys()):
                btn = Button(text=i, size_hint_y=None, height=30)
                btn.bind(on_press=lambda btn: self.pass_setting("variable", btn.text))
                btn.bind(on_release=self.var_dropdown.dismiss)
                self.var_dropdown.add_widget(btn)

        self.depth_dropdown = DropDown()
        if isinstance(self.home.file, str) and self.home.nc and self.home.netcdf['z'] != "Select...":
            for i in list(self.home.netcdf['file'][self.home.netcdf['z']].data):
                btn = Button(text=str(i), size_hint_y=None, height=30)
                btn.bind(on_press=lambda btn: self.pass_setting("depth", btn.text))
                btn.bind(on_release=self.depth_dropdown.dismiss)
                self.depth_dropdown.add_widget(btn)

    def pass_setting(self, setting, value):
        self.home.update_settings(setting, value)
