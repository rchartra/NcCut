# SPDX-FileCopyrightText: 2024 University of Washington
#
# SPDX-License-Identifier: BSD-3-Clause

"""
Functionality for the setting dropdown menus.

Creates the dropdown lists for the various setting dropdown menus. Manages the execution
of setting changes when they occur. This module only defines the dynamic aspect of the menus.
Static aspects are in the nccut.kv file.
"""

from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.app import App
from kivy.metrics import dp
import nccut.functions as func
import os


class LineColorDropDown(DropDown):
    """
    Dynamic elements of the line color drop down menu.

    Attributes:
        app: Reference to current running app
        home: Reference to root :class:`nccut.homescreen.HomeScreen` instance
    """
    def __init__(self, **kwargs):
        """
        Connects to root HomeScreen instance
        """
        super(LineColorDropDown, self).__init__(**kwargs)
        self.home = App.get_running_app().root.get_screen("HomeScreen")

    def pass_setting(self, line_color):
        """
        Passes new line color to display

        Args:
            line_color (str): New line color. Either Blue, Orange, or Green.
        """
        if self.home.file_on:
            new_path = os.path.join(self.home.btn_img_path, line_color.lower() + "_line_btn.png")
            self.home.settings_bar.set_line_color_btn(new_path)
            self.home.display.update_settings("l_color", line_color)


class CircleSizeDropDown(DropDown):
    """
    Dynamic elements of the circle size drop down menu.

    Attributes:
        home: Reference to root :class:`nccut.homescreen.HomeScreen` instance
    """
    def __init__(self, **kwargs):
        """
        Connects to root HomeScreen instance and sets initial slider value
        """
        super(CircleSizeDropDown, self).__init__(**kwargs)
        self.home = App.get_running_app().root.get_screen("HomeScreen")
        if self.home.file_on:
            self.ids.cir_size_slider.value = str(int(self.home.display.cir_size))

    def pass_setting(self, cir_size):
        """
        Pass new circle size to display.

        Args:
            cir_size: New circle size value
        """
        if self.home.file_on:
            self.home.display.update_settings("cir_size", cir_size)


class NetCDFDropDown(DropDown):
    """
    Dynamic elements of the NetCDF setting menu

    Creates all dropdown lists and executes all setting changes. Other settings are
    defined statically in nccut.kv file.

    Attributes:
        home: Reference to root :class:`nccut.homescreen.HomeScreen` instance
        font: Font size for app
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
        self.font = self.home.font
        if self.home.file_on:
            f_type = self.home.display.f_type
        else:
            f_type = None

        self.cmap_dropdown = DropDown()
        if self.home.file_on and f_type == "netcdf":
            for i in self.home.display.cmaps:
                btn = Button(text=i, size_hint_y=None, height=dp(20) + self.font, font_size=self.font)
                btn.bind(on_release=lambda btn: self.pass_setting("colormap", btn.text),  # Setting name: 'colormap'
                         on_press=self.cmap_dropdown.dismiss)
                self.cmap_dropdown.add_widget(btn)

        self.var_dropdown = DropDown()
        if self.home.file_on and f_type == "netcdf":
            for i in list(self.home.display.config["netcdf"]["data"].keys()):
                btn = Button(text=i, size_hint_y=None, height=dp(20) + self.font,
                             halign='center', valign='middle', shorten=True, font_size=self.font)
                btn.bind(on_press=lambda btn: self.pass_setting("variable", btn.text), size=func.text_wrap,
                         on_release=self.var_dropdown.dismiss)  # Setting name: 'variable'
                self.var_dropdown.add_widget(btn)

        self.depth_dropdown = DropDown()
        if self.home.file_on and f_type == "netcdf" and self.home.display.config['netcdf']['z'] != "N/A":
            for i in list(self.home.display.config["netcdf"]['data'][self.home.display.config["netcdf"]['z']].data):
                btn = Button(text=str(i), size_hint_y=None, height=dp(20) + self.font, halign='center', valign='middle',
                             shorten=True, font_size=self.font)
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
