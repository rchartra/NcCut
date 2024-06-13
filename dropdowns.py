"""
Functionality for View and NetCDF setting menus.

Creates the dropdown lists for the 'View' and 'NetCDF' setting menus. Manages the execution
of setting changes when they occur. This module only defines the dynamic aspect of the menus.
Static aspects are in the cutview.kv file.
"""

from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.app import App
import xarray as xr


class ViewDropDown(DropDown):
    """
    Dynamic elements of the 'View' settings menu.

    Creates the line color dropdown menu and manages the execution of all setting options.

    Attributes:
        home: Reference to root HomeScreen instance
        l_color_drop: Line color selection kivy.uix.dropdown.Dropdown object

        Inherits additional attributes from kivy.uix.dropdown.Dropdown (see kivy docs)
    """

    def __init__(self, **kwargs):
        """
        Connects to root HomeScreen instance and creates line color dropdown.
        """
        super(ViewDropDown, self).__init__(**kwargs)
        self.home = App.get_running_app().root.get_screen("HomeScreen")

        col_list = ["Blue", "Orange", "Green"]
        self.l_color_drop = DropDown()
        for i in col_list:
            btn = Button(text=i, size_hint_y=None, height=30)
            btn.bind(on_release=lambda btn: self.pass_setting("l_color", btn.text))  # Setting name: 'l_color'
            btn.bind(on_press=self.l_color_drop.dismiss)
            self.l_color_drop.add_widget(btn)

    def pass_setting(self, setting, value):
        """
        Passes setting changes to the HomeScreen instance.

        Args:
            setting: String name of setting being changed.
            value: New setting value of appropriate data type for setting
        """
        self.home.update_settings(setting, value)

    def rotate(self):
        """
        Call for a 45 degree rotation of current image or NetCDF file by 45 degrees
        """
        if self.home.fileon:
            self.home.img.rotate()

    def flip_v(self):
        """
        Call for a vertical flip of view of current image or NetCDF file
        """
        if self.home.fileon:
            self.home.img.flip_vertically()

    def flip_h(self):
        """
        Call for a horizontal flip of view of current image or NetCDF file
        """
        if self.home.fileon:
            self.home.img.flip_horizontally()


class NetCDFDropDown(DropDown):
    """
    Dynamic elements of the NetCDF setting menu

    Creates all dropdown lists and executes all setting changes. Other settings are
    defined statically in cutview.kv file.

    Attributes:
        home: Reference to root HomeScreen instance
        cmap_dropdown: Color map selection kivy.uix.dropdown.Dropdown object
        var_dropdown: Variable selection kivy.uix.dropdown.Dropdown object
        depth_dropdown: Z dimension value selection kivy.uix.dropdown.Dropdown object

        Inherits additional attributes from kivy.uix.dropdown.Dropdown (see kivy docs)
    """
    def __init__(self, **kwargs):
        """
        Connects to root HomeScreen instance and defines dropdown menus.

        Colormaps are defined in HomeScreen class. Variables and z dimension values come from the
        currently loaded NetCDF file.
        """
        super(NetCDFDropDown, self).__init__(**kwargs)
        self.home = App.get_running_app().root.get_screen("HomeScreen")

        self.cmap_dropdown = DropDown()
        for i in list(self.home.cmaps.keys()):
            btn = Button(text=i, size_hint_y=None, height=30)
            btn.bind(on_release=lambda btn: self.pass_setting("colormap", btn.text))  # Setting name: 'colormap'
            btn.bind(on_press=self.cmap_dropdown.dismiss)
            self.cmap_dropdown.add_widget(btn)

        self.var_dropdown = DropDown()
        if isinstance(self.home.file, str) and self.home.nc:
            for i in list(xr.open_dataset(self.home.file).keys()):
                btn = Button(text=i, size_hint_y=None, height=30)
                btn.bind(on_press=lambda btn: self.pass_setting("variable", btn.text))  # Setting name: 'variable'
                btn.bind(on_release=self.var_dropdown.dismiss)
                self.var_dropdown.add_widget(btn)

        self.depth_dropdown = DropDown()
        if isinstance(self.home.file, str) and self.home.nc and self.home.netcdf['z'] != "Select...":
            for i in list(self.home.netcdf['file'][self.home.netcdf['z']].data):
                btn = Button(text=str(i), size_hint_y=None, height=30)
                btn.bind(on_press=lambda btn: self.pass_setting("depth", btn.text))  # Setting name: 'depth'
                btn.bind(on_release=self.depth_dropdown.dismiss)
                self.depth_dropdown.add_widget(btn)

    def pass_setting(self, setting, value):
        """
        Pass setting changes to home screen.

        Args:
            setting: String name of setting being changed.
            value: New setting value of appropriate data type for setting
        """
        self.home.update_settings(setting, value)
