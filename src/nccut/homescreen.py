# SPDX-FileCopyrightText: 2024 University of Washington
#
# SPDX-License-Identifier: BSD-3-Clause

"""
Functionality for the main screen as well as root of widget tree.

This module manages the functionality of the home screen elements. It also serves as
the root node for the app and passes necessary commands to their appropriate recipient
further down the tree.

"""
import kivy
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
import re
import os
import nccut.functions as func
from nccut.plotpopup import PlotPopup
from pathlib import Path
from plyer import filechooser
from nccut.filedisplay import FileDisplay
from nccut.netcdfconfig import NetCDFConfig
from nccut.settingsbar import SettingsBar


class HomeScreen(Screen):
    """
    Manages the dynamic functionality of the main screen UI elements. Creates and calls upon other modules
    to execute GUI operations.

    Attributes:
        file_on (bool): Whether there is a file currently loaded in viewer
        loaded (bool): Whether the window has fully loaded
        win_load_size: Height and width of fully loaded window on Windows OS
        rel_path: pathlib.Path object to use as output directory
        font (float): Current font size for all buttons
        display: FileDisplay object (draggable image) created when a file is loaded
        nc_popup: Reference to NetCDF configuration popup
        plot_popup: Plotting popup, held here so can be loaded in testing framework
        file: File if one was given on start up from command line, otherwise None
        color_bar_box: BoxLayout containing colorbar and related graphics
        cb_bg: Background for colorbar box
        netcdf_info: Label object containing information about NetCDF file if it has necessary attributes
        sidebar_label: Label object for title of dynamic sidebar
        sidebar_spacer: Spacer to fill any remaining area in dynamic sidebar not filled by widgets
        settings_bar: SettingsBar object holding view manipulation buttons and NetCDF menu
    """
    def __init__(self, btn_img_path, file=None, conf=None, **kwargs):
        """
        Initialize main screen with default settings.

        Creates editing buttons, most UI elements defined in nccut.kv

        Args:
            btn_img_path: Path to location of settings bar button icons
            file: (Optional) File if one was given on start up from command line, otherwise None
            conf: Dictionary of default configuration values
        """
        super(HomeScreen, self).__init__(**kwargs)
        self.general_config = conf
        self.btn_img_path = btn_img_path
        self.file_on = False
        self.loaded = False
        self.rel_path = Path(os.getcwd())
        self.font = self.ids.sidebar_label.font_size
        self.display = None
        self.nc_popup = None
        self.plot_popup = PlotPopup()
        self.file = file
        self.color_bar_box = BoxLayout(size_hint=(0.1, 1), padding=dp(3))
        with self.color_bar_box.canvas:
            Color(0.1, 0.1, 0.1)
            self.cb_bg = RoundedRectangle(size=self.color_bar_box.size, pos=self.color_bar_box.pos, radius=[dp(10),])
        self.color_bar_box.bind(size=self.update_cb_bg, pos=self.update_cb_bg)
        self.netcdf_info = func.BackgroundLabel(text="", font_size=self.font, size_hint_y=None, markup=True,
                                                height=dp(30) + self.font, background_color=[0.1, 0.1, 0.1, 1])
        # Dynamic sidebar
        self.sidebar_label = self.ids.sidebar_label
        self.sidebar_spacer = Widget(size_hint=(1, 0.9))
        self.ids.dynamic_sidebar.add_widget(self.sidebar_spacer)
        # Settings bar
        self.settings_bar = SettingsBar(self.font, self)

    def populate_dynamic_sidebar(self, elements, sidebar_label):
        """
        Removes current sidebar elements and replaces them with the widgets provided.

        Args:
            elements (list): List of widgets to add
            sidebar_label (str): Title for dynamic sidebar
        """
        dsl = self.ids.dynamic_sidebar
        for i in range(len(dsl.children) - 1):
            dsl.remove_widget(dsl.children[0])
        self.sidebar_label.text = sidebar_label
        y_space = 1 - ((len(elements) + 1) * 0.1)
        if y_space < 0:
            y_space = 0
        self.sidebar_spacer.size_hint = (1, y_space)
        for el in elements:
            dsl.add_widget(el)
        dsl.add_widget(self.sidebar_spacer)
        self.font_adapt()

    def update_cb_bg(self, *args):
        """
        Update size and position of color bar box when app window is resized

        Args:
            args: 2 element list of object and the new size/position
        """
        self.cb_bg.pos = self.color_bar_box.pos
        self.cb_bg.size = self.color_bar_box.size

    def initial_load(self):
        """
        If a file was given on start up, wait until app is fully loaded and then load given file.
        """
        if not self.loaded and self.ids.view_box.size[0] / kivy.core.window.Window.size[0] >= 0.75:
            if self.file:
                self.ids.file_in.text = str(self.file)
                self.load_btn()
                if str(self.file)[-3:] == ".nc":
                    self.nc_popup.load.dispatch("on_press")
            self.loaded = True

    def font_adapt(self):
        """
        Updates font size throughout widget tree to the size automatically determined for static UI elements.

        When the window is resized Kivy automatically updates the font size of UI elements defined in nccut.kv
        but not those defined in scripts. Thus this method updates font size for such elements to be the same as
        the static elements.
        """
        font = self.ids.load_btn.font_size
        dsl = self.ids.dynamic_sidebar
        for i in range(len(dsl.children)):
            dsl.children[i].font_size = font
        self.font = font
        self.netcdf_info.font_size = font
        self.settings_bar.font_adapt(font)
        self.plot_popup.font_adapt(font)
        if self.file_on:
            self.display.font_adapt(font)

    def load_btn(self):
        """
        If file name is valid and exists, load image or NetCDF File.

        If a file and any transect tools are already loaded, first clears viewer.
        """
        if self.file_on:
            self.clean_file()
        self.ids.file_in.text = self.ids.file_in.text.strip()
        file = self.ids.file_in.text
        # Limit file names to alphanumeric characters and _-./
        if file == "" or len(re.findall(r'[^A-Za-z0-9_:\\.\-/]', file)) > 0:
            func.alert("Invalid File Name", self)
            self.clean_file()
        else:
            try:
                open(file)
                if file[-3:] == ".nc":
                    # Creates selection popup for nc file data sets
                    self.nc_popup = NetCDFConfig(file, self, self.general_config["netcdf"]["dimension_order"])

                elif file[-5:] == ".jpeg" or file[-4:] == ".png" or file[-4:] == ".jpg":
                    # Creates interactive image from .jpg/.png/.jpeg files
                    self.display = FileDisplay(home=self, f_config={"image": str(file)},
                                               g_config=self.general_config["graphics_defaults"],
                                               t_config=self.general_config["tool_defaults"])
                    self.ids.view.add_widget(self.display)
                    if self.settings_bar.parent is None:
                        self.ids.settings_bar.add_widget(self.settings_bar)
                    self.file_on = True
                else:
                    func.alert("Unsupported File Type", self)
                    self.clean_file()

            except FileNotFoundError:
                func.alert("File Not Found", self)
                self.clean_file()

    def browse(self):
        """
        Opens native operating system file browser to allow user to select their file
        """
        files = filechooser.open_file(filters=[["Valid Files", "*.png", "*.jpg", "*.jpeg", "*.nc"]])
        if files is not None and len(files) > 0:
            self.ids.file_in.text = files[0]
            self.load_btn()

    def load_colorbar_and_info(self, colorbar, config):
        """
        Adds colorbar image and NetCDF file information bar to viewer.

        Args:
            colorbar: kivy.uix.image.Image, colorbar graphic
            config (dict): A dictionary holding info about the file necessary for loading, updating, and accessing data from
                the file. Highest level should have one key that is the name of the file type ("image" or "netcdf") whose
                value is the necessary configuration settings. For images, the config dictionary has form
                {"image": str(file_path)}. For a netcdf file the value is a dictionary of configuration values (see
                :meth:`nccut.netcdfconfig.NetCDFConfig.check_inputs` for structure of dictionary)
        """
        self.update_colorbar(colorbar)
        var_attrs = config["data"][config["var"]].attrs
        if "long_name" in list(var_attrs.keys()):
            v_text = var_attrs["long_name"].title()
        else:
            v_text = config["var"].title()
        if "units" in list(var_attrs.keys()):
            v_text += " (" + var_attrs["units"] + ")"
        if config["z"] != "N/A":
            z_attrs = config["data"][config["z"]].attrs
            if "long_name" in list(z_attrs.keys()):
                z_text = ", " + z_attrs["long_name"].title()
            else:
                z_text = ", " + config["z"].title()
            if "units" in list(z_attrs.keys()):
                z_text += " (" + z_attrs["units"].title() + ")"
            z_text += ": " + config["z_val"]
        else:
            z_text = ""
        self.netcdf_info.text = "[b]" + v_text + z_text + "[/b]"
        self.font_adapt()

    def update_colorbar(self, colorbar):
        """
        Changes colorbar to new colorbar

        Args:
            colorbar: kivy.uix.image.Image, colorbar graphic
        """
        if len(self.ids.view_box.children) == 1:
            self.ids.view_box.add_widget(self.color_bar_box, 1)
            self.ids.main_box.add_widget(self.netcdf_info, 2)
        else:
            self.color_bar_box.remove_widget(self.color_bar_box.children[0])
        self.color_bar_box.add_widget(colorbar)

    def load_netcdf(self, config):
        """
        Load NetCDF file

        Args:
            config (dict): Dictionary of verified NetCDF file configuration settings. Check FileDisplay for more details
        """
        self.display = FileDisplay(home=self, f_config={"netcdf": config},
                                   g_config=self.general_config["graphics_defaults"],
                                   t_config=self.general_config["tool_defaults"])
        self.ids.view.add_widget(self.display)
        if self.settings_bar.parent is None:
            self.ids.settings_bar.add_widget(self.settings_bar)
        self.settings_bar.add_netcdf_button()
        self.settings_bar.font_adapt(self.font)
        self.file_on = True

    def clean_file(self):
        """
        Resets file related attributes.
        """
        kivy.core.window.Window.set_system_cursor("arrow")
        if len(self.ids.view_box.children) > 1:
            self.color_bar_box.remove_widget(self.color_bar_box.children[0])
            self.ids.view_box.remove_widget(self.color_bar_box)
        if len(self.ids.main_box.children) > 3:
            self.ids.main_box.remove_widget(self.netcdf_info)
        if self.file_on:
            self.ids.view.unbind(size=self.display.resize_to_fit)
            def_img_name = self.general_config["graphics_defaults"]["line_color"].lower() + "_line_btn.png"
            self.settings_bar.set_line_color_btn(os.path.join(self.btn_img_path, def_img_name))
            self.display.parent.remove_widget(self.display)
        if self.settings_bar.parent is not None:
            self.ids.settings_bar.remove_widget(self.settings_bar)
        self.settings_bar.remove_netcdf_button()
        self.file_on = False

    def canvas_remove(self, item, *largs):
        """
        Allows external sources to clear canvas.

        Args:
            item: Canvas item to be removed
            *largs: Any other args that are passed

        """
        self.canvas.remove(item)
