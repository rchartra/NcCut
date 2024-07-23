"""
Functionality for the main screen as well as root of widget tree.

This module manages the functionality of the home screen elements. It also serves as
the root node for the app and passes necessary commands to their appropriate recipient
further down the tree.

"""
import kivy
from kivy.app import App
from kivy.uix.screenmanager import Screen
import re
import os
import nccut.functions as func
from pathlib import Path
from nccut.filedisplay import FileDisplay
from nccut.netcdfconfig import NetCDFConfig


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
        file: File if one was given on start up from command line, otherwise None
    """
    def __init__(self, file=None, **kwargs):
        """
        Initialize main screen with default settings.

        Creates editing buttons, most UI elements defined in nccut.kv

        Args:
            file: (Optional) File if one was given on start up from command line, otherwise None
        """
        super(HomeScreen, self).__init__(**kwargs)
        self.file_on = False
        self.loaded = False
        self.rel_path = Path(os.getcwd())
        self.font = self.ids.transect.font_size
        self.display = None
        self.nc_popup = None
        self.file = file

    def initial_load(self):
        """
        If a file was given on start up, wait until app is fully loaded and then load given file.
        """
        if not self.loaded and self.ids.view.size[0] / kivy.core.window.Window.size[0] >= 0.75:
            if self.file:
                self.ids.file_in.text = str(self.file)
                self.go_btn()
                if str(self.file)[-3:] == ".nc":
                    self.nc_popup.go.dispatch("on_press")
            self.loaded = True

    def font_adapt(self):
        """
        Updates font size throughout widget tree to the size automatically determined for static UI elements.

        When the window is resized Kivy automatically updates the font size of UI elements defined in nccut.kv
        but not those defined in scripts. Thus this method updates font size for such elements to be the same as
        the static elements.
        """
        font = self.ids.transect.font_size

        self.font = font
        self.ids.view_btn.font_size = font
        self.ids.netcdf_btn.font_size = font
        if self.file_on:
            self.display.font_adapt(font)

    def transect_btn(self, t_type):
        """
        Calls for the creation and deletion of tools.
        Args:
            t_type (str): Tool type: 'transect' or 'transect_marker'
        """
        if self.file_on:
            self.font_adapt()
            self.display.manage_tool(t_type)

    def go_btn(self):
        """
        If file name is valid and exists, load image or NetCDF File.

        If a file and any transect tools are already loaded, first clears viewer.
        """
        if self.file_on:
            self.display.reset_sidebar()
            self.clean_file()

        file = self.ids.file_in.text

        # Limit file names to alphanumeric characters and _-./
        if file == "" or len(re.findall(r'[^A-Za-z0-9_:\\.\-/]', file)) > 0:
            func.alert("Invalid File Name", self)
            self.clean_file()
        else:
            if len(file) >= 1:
                try:
                    open(file)
                    if file[-3:] == ".nc":
                        # Creates selection popup for nc file data sets
                        self.nc_popup = NetCDFConfig(file, self)

                    elif file[-5:] == ".jpeg" or file[-4:] == ".png" or file[-4:] == ".jpg":
                        # Creates interactive image from .jpg/.png/.jpeg files
                        self.display = FileDisplay(home=self, f_config={"image": str(file)})
                        self.ids.view.add_widget(self.display)
                        self.file_on = True
                    else:
                        func.alert("Unsupported File Type", self)
                        self.clean_file()

                except FileNotFoundError:
                    func.alert("File Not Found", self)
                    self.clean_file()

    def load_netcdf(self, config):
        """
        Load NetCDF file

        Args:
            config (dict): Dictionary of verified NetCDF file configuration settings. Check FileDisplay for more details
        """
        self.display = FileDisplay(home=self, f_config={"netcdf": config})
        self.ids.view.add_widget(self.display)
        self.file_on = True

    def clean_file(self):
        """
        Resets file related attributes.
        """
        kivy.core.window.Window.set_system_cursor("arrow")
        if len(self.ids.colorbar.children) != 0:
            self.ids.colorbar.remove_widget(self.ids.colorbar.children[0])
        if self.file_on:
            self.display.parent.remove_widget(self.display)
        self.file_on = False

    def canvas_remove(self, item, *largs):
        """
        Allows external sources to clear canvas.

        Args:
            item: Canvas item to be removed
            *largs: Any other args that are passed

        """
        self.canvas.remove(item)

    def quit_btn(self):
        """
        Quit application
        """
        App.get_running_app().stop()
