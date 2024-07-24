"""
Functionality for View and NetCDF setting menus.

Creates the dropdown lists for the 'View' and 'NetCDF' setting menus. Manages the execution
of setting changes when they occur. This module only defines the dynamic aspect of the menus.
Static aspects are in the nccut.kv file.
"""

from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.app import App
from kivy.metrics import dp
import nccut.functions as func


class ViewDropDown(DropDown):
    """
    Dynamic elements of the 'View' settings menu.

    Creates the line color dropdown menu and manages the execution of all setting options.

    Attributes:
        home: Reference to root :class:`nccut.homescreen.HomeScreen` instance
        l_color_drop: Line color selection kivy.uix.dropdown.Dropdown object
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
            btn = Button(text=i, size_hint_y=None, height=dp(30))
            btn.bind(on_release=lambda btn: self.pass_setting("l_color", btn.text))  # Setting name: 'l_color'
            btn.bind(on_press=self.l_color_drop.dismiss)
            self.l_color_drop.add_widget(btn)

    def pass_setting(self, setting, value):
        """
        Passes setting changes to the viewer.

        Args:
            setting (str): Name of setting being changed.
            value: New setting value of appropriate data type for setting
        """
        if self.home.file_on:
            self.home.display.update_settings(setting, value)

    def rotate(self):
        """
        Call for a 45 degree rotation of current display by 45 degrees
        """
        if self.home.file_on:
            self.home.display.rotate()

    def flip_v(self):
        """
        Call for a vertical flip of view of current display
        """
        if self.home.file_on:
            self.home.display.flip_vertically()

    def flip_h(self):
        """
        Call for a horizontal flip of view of current display
        """
        if self.home.file_on:
            self.home.display.flip_horizontally()


class NetCDFDropDown(DropDown):
    """
    Dynamic elements of the NetCDF setting menu

    Creates all dropdown lists and executes all setting changes. Other settings are
    defined statically in nccut.kv file.

    Attributes:
        home: Reference to root :class:`nccut.homescreen.HomeScreen` instance
        cmap_dropdown: Color map selection kivy.uix.dropdown.Dropdown object
        var_dropdown: Variable selection kivy.uix.dropdown.Dropdown object
        depth_dropdown: Z dimension value selection kivy.uix.dropdown.Dropdown object
    """
    def __init__(self, **kwargs):
        """
        Connects to root HomeScreen instance and defines dropdown menus.

        Colormaps are defined in :class:`nccut.filedisplay.FileDisplay` class. Variables and z dimension values come
        from the currently loaded NetCDF file.
        """
        super(NetCDFDropDown, self).__init__(**kwargs)
        self.home = App.get_running_app().root.get_screen("HomeScreen")
        if self.home.file_on:
            f_type = self.home.display.f_type
        else:
            f_type = None

        self.cmap_dropdown = DropDown()
        if self.home.file_on and f_type == "netcdf":
            for i in list(self.home.display.cmaps.keys()):
                btn = Button(text=i, size_hint_y=None, height=dp(30))
                btn.bind(on_release=lambda btn: self.pass_setting("colormap", btn.text),  # Setting name: 'colormap'
                         on_press=self.cmap_dropdown.dismiss)
                self.cmap_dropdown.add_widget(btn)

        self.var_dropdown = DropDown()
        if self.home.file_on and f_type == "netcdf":
            for i in list(self.home.display.config["netcdf"]["file"].keys()):
                btn = Button(text=i, size_hint_y=None, height=dp(30), halign='center', valign='middle', shorten=True)
                btn.bind(on_press=lambda btn: self.pass_setting("variable", btn.text), size=func.text_wrap,
                         on_release=self.var_dropdown.dismiss)  # Setting name: 'variable'
                self.var_dropdown.add_widget(btn)

        self.depth_dropdown = DropDown()
        if self.home.file_on and f_type == "netcdf" and self.home.display.config['netcdf']['z'] != "N/A":
            for i in list(self.home.display.config["netcdf"]['file'][self.home.display.config["netcdf"]['z']].data):
                btn = Button(text=str(i), size_hint_y=None, height=dp(30), halign='center', valign='middle',
                             shorten=True)
                btn.bind(on_press=lambda btn: self.pass_setting("depth", btn.text), size=func.text_wrap,
                         on_release=self.depth_dropdown.dismiss)  # Setting name: 'depth'
                self.depth_dropdown.add_widget(btn)

    def pass_setting(self, setting, value):
        """
        Pass setting changes to display.

        Args:
            setting (str): Name of setting being changed.
            value: New setting value of appropriate data type for setting
        """
        if self.home.file_on:
            self.home.display.update_settings(setting, value)
