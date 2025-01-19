"""
UI and functionality for plotting and saving popup.

Creates UI elements of the popup and manages the creation of plots based on user input.
Manages the saving of the plots and user selected data.
"""

import io
import kivy.uix as ui
from kivy.lang import Builder
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.checkbox import CheckBox
from kivy.uix.dropdown import DropDown
from kivy.uix.textinput import TextInput
from plyer import filechooser
import nccut.functions as func
from nccut.plotwindow import PlotWindow
from kivy.core.image import Image as CoreImage
import matplotlib.pyplot as plt
from PIL import Image as im
from scipy.interpolate import RegularGridInterpolator
import numpy as np
import copy
import pandas as pd
import datetime
import json
import pathlib
import os
import re
import platform
import subprocess


KV_FILE_PATH = pathlib.Path(__file__).parent.resolve() / "plotpopup.kv"
Builder.load_file(str(KV_FILE_PATH))


class BackgroundDropDown(DropDown):
    """
    General class for a dropdown menu with a background color

    Attributes:
        rect: Rectangle object that serves as background to the dropdown.
    """
    def open_obj(self, obj, widget):
        """
        Calls for open even when passed object by Kivy

        Args:
            obj: Instance of object that called it... redundant in this case
            widget: RoundedButton to which dropdown is bound
        """
        self.open(widget)

    def open(self, widget):
        """
        Overwrites DropDown open method to also draw a background rectangle.

        Args:
            widget: RoundedButton to which dropdown is bound
        """
        super(BackgroundDropDown, self).open(widget)
        with self.canvas.before:
            Color(rgb=[0.25, 0.25, 0.25])
            self.rect = Rectangle(size=self.size, pos=self.pos, radius=[dp(10), ])
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        """
        Update graphics if window size is changed
        """
        self.rect.pos = self.pos
        self.rect.size = self.size


class PlotPopup(Popup):
    """
    Popup with plotting and saving selections.

    Creates UI elements of the popup, creates plots according to user selections, and saves
    plots and/or selected data.

    Attributes:
        is_open (bool): Whether popup is currently open
        home: Reference to root :class:`nccut.homescreen.HomeScreen` instance.
        all_transects (dict): Dictionary of data from all transects marked out by the user.
        t_type (str): 'Orthogonal' if transects came from orthogonal chain tool or 'Inline' if transects came from
            inline chain tool
        active_transects (dict): Dictionary of currently selected transects. 'Click <X Cord>', 'Click <Y Cord>', and
            'Width' fields should be removed (if orthogonal chain tool) to simplify plotting. Contains average
            of transects if orthogonal chain tool was used with a constant transect width.
        f_type (str): If file is NetCDF file: 'netcdf'. If file is a JPG or PNG: 'image'.
        config (dict): Information necessary for accessing the file. For images this is the file path and for NetCDF
            files this is a dictionary of configuration values (see
            :meth:`nccut.netcdfconfig.NetCDFConfig.check_inputs` for structure of dictionary)
        active_z (list): List of selected Z values. Empty list if 2D NetCDF or Image file.
        active_vars (list): List of selected variables. Empty list if image file.
        active_data: Currently plotted data
        b_height (int): Button height, adapts to font size
        plot: Image containing plot.
        plotting: BoxLayout that holds plot and selection sidebar.
        title (str): Popup title
        content: BoxLayout containing all UI elements in popup
        size_hint (tuple): (width, height) of relative size of popup to window
        buttons: BoxLayout containing the save buttons and the close button
        f_m: Multiplier for the font size for the save buttons since they need to be slightly smaller
        t_select: RoundedButton which opens transect selection dropdown menu
        widgets_with_text: List of widgets with text whose font size must be updated when the window is resized
        v_select: RoundedButton which opens variable selection dropdown menu (Only if NetCDF file)
        z_select: RoundedButton which opens z value selection dropdown menu (Only if 3D NetCDF file)
        t_drop: Transect dropdown
        v_drop: Variable dropdown
        z_drop: Z Value dropdown
    """

    def __init__(self, **kwargs):
        super(PlotPopup, self).__init__(**kwargs)
        """
        Initializes attributes. They are loaded later when popup is actually opened.
        """
        self.is_open = False
        self.bind(on_dismiss=self.close)
        self.all_transects = None
        self.home = None
        self.font = None
        self.f_type = None
        self.config = None
        self.t_type = None
        self.active_transects = None
        self.active_vars = None
        self.active_z = None
        self.active_data = None
        self.b_height = None
        self.plot = None
        self.f_m = None
        self.t_select = None
        self.widgets_with_text = None
        self.allz_btn = None
        self.t_drop = None
        self.v_drop = None
        self.z_drop = None
        self.v_select = None
        self.z_select = None

    def close(self, *args):
        """
        Cleans up popup and marks it as closed
        :param args:
        :return:
        """
        if self.is_open:
            self.clean()
            self.is_open = False

    def run(self, transects, home, config):
        """
        Defines popup UI elements and opens popup.

        Args:
            transects (dict): Dictionary of transect data from tool which opened popup
            home: Reference to root :class:`nccut.homescreen.HomeScreen` instance.
            config: Dictionary of configuration data for currently loaded file
        """
        self.all_transects = transects
        self.home = home
        self.font = self.home.font
        self.f_type = list(config.keys())[0]
        self.config = config
        if list(self.all_transects.keys())[0][0:-2] == "Orthogonal Chain":
            self.t_type = "Orthogonal"
        elif list(self.all_transects.keys())[0][0:-2] == "Inline Chain":
            self.t_type = "Inline"

        # Create nested dictionary of Booleans indicating which transects are currently selected
        self.active_transects = {}

        act = copy.deepcopy(self.all_transects)
        for key in list(act.keys()):
            self.active_transects[key] = {}
            # Remove fields that don't get plotted
            if self.t_type == "Orthogonal":
                for k in list(act[key].keys())[:3]:
                    act[key].pop(k)
            elif self.t_type == "Inline":
                for k in list(act[key].keys())[:2]:
                    act[key].pop(k)
            self.active_transects[key] = dict.fromkeys(act[key], False)

            # If orthogonal and all values same width, add an average option
            if self.t_type == "Orthogonal":
                w_lis = self.all_transects[key]['Width']
                if all(x == w_lis[0] for x in w_lis):
                    new = {"Average": False}
                    new.update(self.active_transects[key])
                    self.active_transects[key] = new

        # Start with the first group selected
        first = list(self.active_transects.keys())[0]
        self.active_transects[first] = dict.fromkeys(self.active_transects[first], True)

        # If orthogonal chain start with average not selected
        if self.t_type == "Orthogonal":
            w_lis = self.all_transects[first]['Width']
            if all(x == w_lis[0] for x in w_lis):
                self.active_transects[first]["Average"] = False

        # Initialize dropdown selections
        if self.f_type == "netcdf":
            if self.config[self.f_type]['z'] == "N/A":
                self.active_z = []
            else:
                self.active_z = [self.config[self.f_type]['z_val']]
            self.active_vars = [self.config[self.f_type]["var"]]
        else:
            self.active_vars = []
            self.active_z = []

        # Get plot for initial selections
        self.active_data = self.get_data()
        self.plot_active()
        temp = io.BytesIO()
        plt.savefig(temp, format="png")
        temp.seek(0)
        plt.close()

        # Popup Graphics Code
        self.b_height = dp(40) + self.font
        self.plot = ui.image.Image(source="", texture=CoreImage(io.BytesIO(temp.read()), ext="png").texture,
                                   size_hint=(0.6, 1), fit_mode="contain")
        self.ids.plotting.add_widget(self.plot, len(self.ids.plotting.children))
        self.f_m = 0.8
        self.widgets_with_text = [self.ids.sel_transects_label, self.ids.sel_transects_btn]

        # Transect selection
        if self.t_type == "Orthogonal":
            self.t_drop = self.get_orthogonal_chain_dropdown()
        elif self.t_type == "Inline":
            self.t_drop = self.get_inline_chain_dropdown()
        self.ids.sel_transects_btn.fbind("on_press", self.t_drop.open_obj, self.ids.sel_transects_btn)

        if self.f_type == "netcdf":
            # Variable Selection
            v_box = ui.boxlayout.BoxLayout(size_hint=(1, None), spacing=dp(5), height=self.b_height)
            v_lab = Label(text="Select Variables: ", size_hint=(0.5, 1), font_size=self.font, halign='center',
                          valign='middle')
            v_lab.bind(size=func.text_wrap)
            v_box.add_widget(v_lab)
            self.v_select = func.RoundedButton(text="Select...", size_hint=(0.5, 1),
                                               pos_hint={"center_y": 0.5}, font_size=self.font)
            v_box.add_widget(self.v_select)
            self.v_drop = self.get_var_dropdown()
            self.v_select.bind(on_press=lambda x: self.v_drop.open(self.v_select))
            self.ids.sidebar.add_widget(v_box, 1)
            self.widgets_with_text.extend([v_lab, self.v_select])
            if self.config[self.f_type]['z'] != "N/A":
                # Z Selection
                z_box = ui.boxlayout.BoxLayout(size_hint=(1, None), spacing=dp(5), height=self.b_height)
                z_lab = Label(text="Select Z Values: ", size_hint=(0.5, 1), font_size=self.font, halign='center',
                              valign='middle')
                z_lab.bind(size=func.text_wrap)
                z_box.add_widget(z_lab)
                self.z_select = func.RoundedButton(text="Select...", size_hint=(0.5, 1),
                                                   pos_hint={"center_y": 0.5}, font_size=self.font)
                z_box.add_widget(self.z_select)
                self.z_drop = self.get_z_dropdown()
                self.z_select.bind(on_press=lambda x: self.z_drop.open(self.z_select))
                self.ids.sidebar.add_widget(z_box, 1)

                # Plot All Z option only if there is more than one z value
                if len(self.config[self.f_type]["data"][self.config[self.f_type]['z']].data) > 1:
                    zp_box = ui.boxlayout.BoxLayout(size_hint=(1, None), height=self.b_height, padding=dp(10))
                    zp_btn = func.RoundedButton(text="Plot all Z as Img", size_hint=(1, 1), font_size=self.font)
                    zp_btn.bind(on_press=lambda x: self.get_all_z_plot())
                    zp_box.add_widget(zp_btn)
                    self.ids.sidebar.add_widget(zp_box, 1)
                    self.widgets_with_text.append(zp_btn)

                # Export All Z Option
                self.allz_btn = func.RoundedButton(text="All Z Data", size_hint_x=None, width=dp(50) + self.font * 3,
                                                   font_size=self.font)
                self.allz_btn.bind(on_press=lambda x: self.file_input('all_z'))
                self.ids.buttons.add_widget(self.allz_btn)
                self.widgets_with_text.extend([z_lab, self.z_select])
            else:
                # Spacer if 2D NetCDF
                self.ids.sidebar.add_widget(Label(text="", size_hint=(1, 0.6)))
        else:
            # Spacer if Image
            self.ids.sidebar.add_widget(Label(text="", size_hint=(1, 0.8)))
        self.open()
        self.is_open = True
        self.title_size = self.font
        self.font_adapt(self.font)

    def clean(self):
        """
        Cleans plot and optional widgets from plotting popup
        """
        self.ids.plotting.remove_widget(self.plot)
        while len(self.ids.sidebar.children) > 2:
            self.ids.sidebar.remove_widget(self.ids.sidebar.children[1])
        if self.allz_btn:
            self.ids.buttons.remove_widget(self.allz_btn)
            self.allz_btn = None
        self.ids.sel_transects_btn.funbind('on_press', self.t_drop.open_obj, self.ids.sel_transects_btn)

    def font_adapt(self, font):
        """
        Updates font of elements in plotting menu with text and size of dropdown menus.

        Args:
            font (float): New font size
        """
        if self.is_open:
            drop_width = max(Window.size[0] * 0.22, dp(160) + self.font * 4)
            self.t_drop.width = drop_width
            if self.f_type == "netcdf":
                self.v_drop.width = drop_width
                if self.config[self.f_type]['z'] != "N/A":
                    self.z_drop.width = drop_width
            for btn in self.ids.buttons.children:
                btn.font_size = font * self.f_m
            self.ids.close_btn.font_size = font * self.f_m
            for wid in self.widgets_with_text:
                wid.font_size = font

    def file_input(self, s_type):
        """
        Popup window for user to give name for plot/json file to be saved.

        Args:
            s_type (str): String corresponding to what is being saved:
                's_data': Transect data for selections
                'a_data': Transect data for all transects taken
                'all_z': Transect data for selections for all z dimension values
                'png': Current plot as a PNG file
                'pdf': Current plot as a PDF file
        """

        if s_type == "s_data" or s_type == "a_data" or s_type == "all_z":
            f_types = ["*.json"]
        elif s_type == "png":
            f_types = ["*.png"]
        elif s_type == "pdf":
            f_types = ["*.pdf"]
        try:
            if platform.system() == "Darwin":
                # Construct the AppleScript command for prompting for file name
                script = """
                        set file_path to choose file name with prompt "Select a location and enter a filename:"
                        POSIX path of file_path
                        """
                result = subprocess.run(
                    ['osascript', '-e', script],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
                if result.returncode == 0:
                    fpath = result.stdout.strip()
                else:
                    fpath = None
            else:
                fpath = filechooser.save_file(filters=f_types)[0]
            if fpath is not None and len(fpath) > 0:
                if s_type == "s_data":
                    self.download_selected_data(fpath)
                elif s_type == "a_data":
                    self.download_all_data(fpath)
                elif s_type == "all_z":
                    self.download_all_z_data(fpath)
                elif s_type == "png":
                    self.download_png_plot(fpath)
                elif s_type == "pdf":
                    self.download_pdf_plot(fpath)
        except Exception:
            # If native file browser not working, provide manual file entry method
            content = ui.boxlayout.BoxLayout(orientation='horizontal')
            popup = Popup(title="File Name", content=content, size_hint=(0.5, 0.15))
            txt = TextInput(size_hint=(0.7, 1), hint_text="Enter File Name")
            content.add_widget(txt)
            go = Button(text="Ok", size_hint=(0.1, 1))
            go.bind(on_press=lambda x: self.manual_file_input(txt.text, s_type))
            go.bind(on_release=popup.dismiss)
            close = Button(text="Close", size_hint=(0.2, 1), font_size=self.home.font)
            close.bind(on_press=popup.dismiss)
            content.add_widget(go)
            content.add_widget(close)
            popup.open()
            return

    def manual_file_input(self, fname, s_type):
        """
        Checks if a filename is valid and prevents overwriting.
        Checks a file name doesn't have any problematic characters. If file name is a file path
        ensures that the directories exists. If a file name is the same as one that already
        exists it adds a (#) to avoid overwriting existing file. Calls for data/plot to be saved to corrected file name.

        Args:
            fname: File name/path given by user
            s_type (str): String corresponding to what is being saved:
                'data': Transect data for selections
                'all_z_data': Transect data for selections for all z dimension values
                'png': Current plot as a PNG file
                'pdf': Current plot as a PDF file
        """

        if s_type == "s_data" or s_type == "a_data" or s_type == "all_z":
            extension = ".json"
        elif s_type == "png":
            extension = ".png"
        elif s_type == "pdf":
            extension = ".pdf"
        path = self.home.rel_path
        if fname.find(".") >= 1:
            fname = fname[:fname.find(".")]
        if fname == "" or len(re.findall(r'[^A-Za-z0-9_\-/:\\]', fname)) > 0:
            func.alert_popup("Invalid file name")
            return False
        if "/" in fname:
            if not pathlib.Path.exists(path / fname[:fname.rfind("/") + 1]):
                func.alert_popup("Directory not found")
                return False

        exist = True
        fcount = 0
        while exist:
            if pathlib.Path.exists(path / (fname + extension)):
                fcount += 1
                if fcount == 1:
                    fname = fname + "(1)"
                else:
                    fname = fname[:fname.find("(") + 1] + str(fcount) + ")"
            else:
                exist = False
        fpath = os.path.abspath(fname + extension)

        if s_type == "s_data":
            self.download_selected_data(fpath)
        elif s_type == "a_data":
            self.download_all_data(fpath)
        elif s_type == "all_z":
            self.download_all_z_data(fpath)
        elif s_type == "png":
            self.download_png_plot(fpath)
        elif s_type == "pdf":
            self.download_pdf_plot(fpath)

    def download_png_plot(self, f_path):
        """
        Download the current plot as a PNG file if valid file name given

        Args:
            f_path (str): Output file path
        """
        if f_path.find(".") == -1:
            f_path = f_path + ".png"
        else:
            f_path = f_path[:f_path.find(".")] + ".png"
        try:
            if isinstance(self.plot, PlotWindow):
                self.plot.export_to_png(f_path)
            else:
                pil_image = im.frombytes('RGBA', self.plot.texture.size, self.plot.texture.pixels)
                pil_image.save(f_path)
            func.alert_popup("Download Complete")
        except Exception as error:
            func.alert_popup(str(error))

    def download_pdf_plot(self, f_path):
        """
        Download the current plot as a PDF file if valid file name given

        Args:
            f_path (str): Output file path
        """
        if f_path.find(".") == -1:
            f_path = f_path + ".pdf"
        else:
            f_path = f_path[:f_path.find(".")] + ".pdf"
        try:
            if isinstance(self.plot, PlotWindow):
                core_img = self.plot.export_as_image()
                image_data = core_img.texture.pixels
                width, height = core_img.size
                image_array = np.frombuffer(image_data, np.uint8).reshape((height, width, 4))
                pil_image = im.fromarray(image_array, 'RGBA')
                pil_image.save(f_path)
            else:
                pil_image = im.frombytes('RGBA', self.plot.texture.size, self.plot.texture.pixels)
                pil_image.save(f_path)
            func.alert_popup("Download Complete")
        except Exception as error:
            func.alert_popup(str(error))

    def download_selected_data(self, f_path):
        """
        Downloads selected transect data into a JSON file if valid file name given.

        Args:
            f_path (str): Output file path
        """
        if f_path.find(".") == -1:
            f_path = f_path + ".json"
        else:
            f_path = f_path[:f_path.find(".")] + ".json"
        try:
            dat = copy.deepcopy(self.active_data)
            if len(self.active_vars) == 0:  # If Image
                final = self.add_group_info(dat)
            elif len(self.active_z) == 0:  # If 2D NetCDF
                final = {}
                for var in list(dat.keys()):
                    final[var] = self.add_group_info(dat[var])
            else:  # If 3D NetCDF
                final = {}
                for var in list(dat.keys()):
                    final[var] = {}
                    for z in list(dat[var].keys()):
                        final[var][z] = self.add_group_info(dat[var][z])
            final = self.add_metadata(final)
            with open(f_path, "w") as f:
                json.dump(final, f)

            func.alert_popup("Download Complete")
        except Exception as error:
            func.alert_popup(str(error))

    def download_all_data(self, f_path):
        """
        Downloads selected data for all transects/groups into a JSON file if valid file name given.

        Args:
            f_path (str): Output file path
        """
        try:
            original = copy.copy(self.active_transects)
            for m in list(self.active_transects.keys()):
                for t in list(self.active_transects[m].keys()):
                    self.active_transects[m][t] = True
            self.active_data = self.get_data()
            self.download_selected_data(f_path)
            self.active_transects = original
            self.active_data = self.get_data()
        except Exception as error:
            func.alert_popup(str(error))

    def add_metadata(self, dicti):
        """
        Adds global and variable specific data to an output dictionary.

        Args:
            dicti: Dictionary of data about to be exported

        Returns:
            dicti: Dictionary of data with metadata fields added
        """
        def attrs_to_str(d):
            return {k: str(v) for k, v in d.items()}

        config = self.config[self.f_type]
        # On GitHub Linux Runner a user is not defined resulting in an error
        try:
            user = os.getlogin()
        except OSError:
            user = "_user_id_not_found_"
        global_metadata = {"time_stamp": datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                           "user": user, "license": "CC0-1.0"}
        global_metadata.update(self.home.general_config["metadata"])
        if self.f_type == "netcdf":
            global_metadata["file"] = config["file"]
            global_metadata["netcdf_attrs"] = attrs_to_str(config["data"].attrs)
            dims = {config["x"]: attrs_to_str(config["data"][config["x"]].attrs),
                    config["y"]: attrs_to_str(config["data"][config["y"]].attrs)}
            if config["z"] != "N/A":
                dims[config["z"]] = attrs_to_str(config["data"][config["z"]].attrs)
            global_metadata["dim_attrs"] = dims
            for key in list(dicti.keys()):
                dicti[key][key + "_attrs"] = attrs_to_str(config["data"][key].attrs)
        else:
            global_metadata["file"] = config
        dicti["global_metadata"] = global_metadata
        return dicti

    def add_group_info(self, dicti):
        """
        Adds back fields removed for plotting purposes

        Args:
            dicti (dict): Dictionary of transect data from a single group

        Returns:
            Dictionary of transect data with non-plotted data fields added back in.
        """
        if list(dicti.keys())[0][0:10] == "Orthogonal":
            for o in list(dicti.keys()):
                for key in list(self.all_transects[o].keys())[:3]:
                    dicti[o][key] = list(self.all_transects[o][key])
        elif list(dicti.keys())[0][0:6] == "Inline":
            for i in list(dicti.keys()):
                for key in list(self.all_transects[i].keys())[:2]:
                    dicti[i][key] = list(self.all_transects[i][key])
        return dicti

    def download_all_z_data(self, f_path):
        """
        Get and download data for all selected variables for all z dimension values.

        Args:
            f_path (str): Output file path
        """
        try:
            original = copy.copy(self.active_z)
            z_list = self.config[self.f_type]['z']
            self.active_z = [str(z) for z in self.config[self.f_type]['data'].coords[z_list].data]
            self.active_data = self.get_data()
            self.download_selected_data(f_path)
            self.active_z = original
            self.active_data = self.get_data()
        except Exception as error:
            func.alert_popup(str(error))

    def get_inline_chain_dropdown(self):
        """
        Build dropdown menu for selecting entire inline chains.

        Returns:
            :class:`nccut.plotpopup.BackgroundDropDown` for transect options
        """
        # Get dropdown for chain options
        drop = BackgroundDropDown(auto_width=False, width=dp(180), max_height=dp(200))
        all_box = ui.boxlayout.BoxLayout(spacing=dp(10), padding=dp(10), size_hint_y=None, height=dp(30) + self.font)
        drop.add_widget(all_box)
        all_btn = func.RoundedButton(text="Select All", font_size=self.font)
        for i in list(self.active_transects.keys()):
            c_box = ui.boxlayout.BoxLayout(spacing=dp(5), size_hint_y=None, height=dp(30) + self.font)
            but = Button(text=i, size_hint=(0.5, 1), background_color=[0, 0, 0, 0], font_size=self.font)
            check = CheckBox(active=all(self.active_transects[i].values()), size_hint=(0.5, 1))
            check.bind(active=lambda x, y, t=i: self.on_inline_chain_checkbox(x, t))
            but.bind(on_press=lambda x, c=check: self.on_check_button(c))
            c_box.add_widget(but)
            c_box.add_widget(check)
            drop.add_widget(c_box)
        all_btn.bind(on_press=lambda x: self.select_all(drop.children[0].children[:-1]))
        all_box.add_widget(all_btn)
        return drop

    def on_inline_chain_checkbox(self, check, chain, *args):
        """
        Updates plot when a chain checkbox is clicked. Safeguards so at least one chain
        is always selected.

        Args:
            check: Reference to kivy.uix.checkbox.CheckBox in transect list
            chain (str): Name of chain 'Inline Chain #'
        """
        # Select or deselect chain
        for tran in list(self.active_transects[chain].keys()):
            self.active_transects[chain][tran] = not self.active_transects[chain][tran]

        # Check this isn't the last chain selected
        count = 0
        for key in list(self.active_transects.keys()):
            if all(self.active_transects[key].values()):
                count += 1
        if count == 0:  # If last chain unchecked, recheck and ignore
            for tran in list(self.active_transects[chain].keys()):
                self.active_transects[chain][tran] = not self.active_transects[chain][tran]
            check.active = True
            return
        else:
            # Update current data and plot
            self.active_data = self.get_data()
            self.update_plot()

    def get_orthogonal_chain_dropdown(self):
        """
        Build dropdown menu for orthogonal chains with sub-menus for the individual transects.

        Returns:
            :class:`nccut.plotpopup.BackgroundDropDown` for orthogonal chain options
        """
        # Get dropdown for orthogonal chain options
        chain_list = BackgroundDropDown(auto_width=False, width=dp(180), max_height=dp(300))
        for i in list(self.all_transects.keys()):
            g_box = ui.boxlayout.BoxLayout(spacing=dp(10), padding=dp(10), size_hint_y=None, height=dp(30) + self.font,
                                           width=dp(180))
            btn = func.RoundedButton(text=i, font_size=self.font)
            btn.bind(on_press=lambda but=btn, txt=i: self.transect_drop(txt, but))
            g_box.add_widget(btn)
            chain_list.add_widget(g_box)
        return chain_list

    def transect_drop(self, chain, button):
        """
        Attaches transect dropdowns to orthogonal chain buttons in orthogonal chain dropdown menu

        Args:
            chain (str): Orthogonal chain label. Ex: 'Orthogonal Chain #'
            button: RoundedButton, Orthogonal chain's button in orthogonal chain dropdown menu
        """
        temp_transect_drop = self.get_transect_dropdown(chain)
        temp_transect_drop.open(button)

    def get_transect_dropdown(self, key):
        """
        Build dropdown menu for selecting orthogonal transects from an orthogonal chain.

        Args:
            key (str): Name of orthogonal chain selecting from. Ex: 'Orthogonal Chain #'

        Returns:
            :class:`nccut.plotpopup.BackgroundDropDown` for transect options
        """
        # Get dropdown for transect options
        drop = BackgroundDropDown(auto_width=False, width=dp(180), max_height=dp(200))
        all_box = ui.boxlayout.BoxLayout(spacing=dp(10), padding=dp(10), size_hint_y=None, height=dp(30) + self.font)
        drop.add_widget(all_box)
        all_btn = func.RoundedButton(text="Select All", font_size=self.font)
        for i in list(self.active_transects[key].keys()):
            c_box = ui.boxlayout.BoxLayout(spacing=dp(5), size_hint_y=None, height=dp(30) + self.font, width=dp(180))
            but = Button(text=i, background_color=[0, 0, 0, 0], font_size=self.font)
            check = CheckBox(active=self.active_transects[key][i], size_hint_x=None, width=dp(40))
            check.bind(active=lambda x, y, m=key, t=i: self.on_transect_checkbox(x, m, t))
            but.bind(on_press=lambda x, c=check: self.on_check_button(c))
            c_box.add_widget(but)
            c_box.add_widget(check)
            drop.add_widget(c_box)
        all_btn.bind(on_press=lambda x: self.select_all(drop.children[0].children[:-1]))
        all_box.add_widget(all_btn)
        return drop

    def select_all(self, boxes):
        """
        If all checkboxes are checked, uncheck all boxes. Otherwise, check all boxes. If a box is the only box checked
        across all groups it will remain checked no matter what.

        Args:
            boxes: List of BoxLayouts containing checkbox widgets
        """
        all_true = True
        for c_box in boxes:
            if not c_box.children[0].active:
                c_box.children[0].active = not c_box.children[0].active
                all_true = False
        if all_true:
            for c_box in boxes:
                c_box.children[0].active = False

    def on_transect_checkbox(self, check, chain, transect, *args):
        """
        Updates plot when a transect checkbox is clicked. Safeguards so at least one transect
        is always selected.

        Args:
            check: Reference to kivy.uix.checkbox.CheckBox in transect list
            chain (str): Name of orthogonal chain selecting from. Ex: 'Orthogonal Chain #'
            transect (str): Name of transect 'Cut #'
        """
        # Select or deselect transect
        self.active_transects[chain][transect] = not self.active_transects[chain][transect]

        # Check this isn't the last transect selected
        count = 0
        for key in list(self.active_transects.keys()):  # Count current transects
            count += sum(self.active_transects[key].values())
        if count == 0:  # If last transect unchecked, recheck and ignore
            self.active_transects[chain][transect] = not self.active_transects[chain][transect]
            check.active = True
            return
        else:
            # Update current data and plot
            self.active_data = self.get_data()
            self.update_plot()

    def get_var_dropdown(self):
        """
        Get dropdown for NetCDF variable options. Variable only available if dimensions match current variable

        Returns:
            :class:`nccut.plotpopup.BackgroundDropdown` menu of variable options
        """
        file = self.config[self.f_type]['data']
        var_list = BackgroundDropDown(auto_width=False, width=dp(180), max_height=dp(300))
        for var in list(file.keys()):
            if file[self.config[self.f_type]['var']].dims == file[var].dims:  # Dimensions must match variable in viewer
                v_box = ui.boxlayout.BoxLayout(spacing=dp(3), padding=dp(5), size_hint_y=None,
                                               height=dp(30) + self.font)
                but = Button(text=var, halign='center', valign='middle', shorten=True, font_size=self.font,
                             background_color=[0, 0, 0, 0])
                v_box.add_widget(but)
                check = CheckBox(active=var in self.active_vars, size_hint_x=None, width=dp(40))
                check.bind(active=lambda x, y, var=var: self.on_var_checkbox(x, var))
                but.bind(size=func.text_wrap, on_press=lambda x, c=check: self.on_check_button(c))
                v_box.add_widget(check)
                var_list.add_widget(v_box)
        return var_list

    def on_var_checkbox(self, check, var, *args):
        """
        Updates plot when a variable checkbox is clicked. Safeguards so at least one variable
        is always selected.

        Args:
            check: Reference to kivy.uix.checkbox.CheckBox in variable list
            var (str): String, name of variable
        """
        if var in self.active_vars:
            self.active_vars.remove(var)
        else:
            self.active_vars.append(var)

        if not self.active_vars:  # If last variable add variable back
            self.active_vars.append(var)
            check.active = True
            return
        self.active_data = self.get_data()
        self.update_plot()

    def get_z_dropdown(self):
        """
        Get dropdown for NetCDF z value selections

        Returns:
            :class:`nccut.plotpopup.BackgroundDropDown` menu of z value options
        """
        z_list = BackgroundDropDown(auto_width=False, width=dp(180), max_height=dp(300))
        for z in list(self.config[self.f_type]['data'].coords[self.config[self.f_type]['z']].data):
            z_box = ui.boxlayout.BoxLayout(spacing=dp(3), padding=dp(5), size_hint_y=None, height=dp(30) + self.font)
            but = Button(text=str(z), halign='center', valign='middle', shorten=True, font_size=self.font,
                         background_color=[0, 0, 0, 0])
            check = CheckBox(active=str(z) in self.active_z, size_hint_x=None, width=dp(40))
            check.bind(active=lambda x, y, z=str(z): self.on_z_checkbox(x, z))
            but.bind(size=func.text_wrap, on_press=lambda x, c=check: self.on_check_button(c))
            z_box.add_widget(but)
            z_box.add_widget(check)
            z_list.add_widget(z_box)
        return z_list

    def on_check_button(self, check, *args):
        """
        Turns checkbox on if off and vice versa

        Args:
            check: kivy.uix.checkbox.CheckBox
            args: Unused arguments passed by button callback
        """
        check.active = not check.active

    def on_z_checkbox(self, check, z, *args):
        """
        Updates plot when a z value checkbox is clicked. Safeguards so at least one z value
        is always selected.

        Args:
            check: Reference to kivy.uix.checkbox.CheckBox in variable list
            z (str): Name of z value
            *args: Unused args passed to method
        """
        if z in self.active_z:
            self.active_z.remove(z)
        else:
            self.active_z.append(z)

        if not self.active_z:  # If last z value add z value back
            self.active_z.append(z)
            check.active = True
            return
        self.active_data = self.get_data()
        self.update_plot()

    def get_all_z_plot(self):
        """
        Determines if settings are okay to do an all z value plot. If so calls for plot, if not creates an error
        popup.
        """
        plot_ok = False
        if self.t_type == "Orthogonal":
            t_count = 0
            for key in list(self.active_transects.keys()):
                # Count current transects selected
                no_avg = copy.copy(self.active_transects[key])
                if "Average" in list(no_avg.keys()):
                    no_avg.pop("Average")
                t_count += sum(no_avg.values())
            if t_count == 1 and len(self.active_vars) == 1:
                plot_ok = True
        elif self.t_type == "Inline":
            c_count = 0
            for key in list(self.active_transects.keys()):
                # Count current chains selected
                c_count += all(self.active_transects[key].values())
            if c_count == 1 and len(self.active_vars) == 1:
                plot_ok = True
        if plot_ok:
            # Go ahead and plot
            try:
                self.ids.plotting.remove_widget(self.plot)
                if self.t_type == "Orthogonal":
                    z_data = self.get_all_z_orthogonal_chain()
                elif self.t_type == "Inline":
                    z_data = self.get_all_z_inline_chain()
                self.plot = PlotWindow(self.config[self.f_type], z_data, self.home.display.colormap, size_hint=(0.7, 1))
                self.plot.bind(size=self.plot.load)
                self.ids.plotting.add_widget(self.plot, len(self.ids.plotting.children))
            except Exception as error:
                func.alert_popup(str(error))
        else:
            # Error popup if more than one transect and/or variable is selected
            content = ui.boxlayout.BoxLayout()
            error = Popup(title="Error", content=content, size_hint=(0.5, 0.15))
            if self.t_type == "Orthogonal":
                text = "transect"
            elif self.t_type == "Inline":
                text = "chain"
            lab = Label(text="Please only select one " + text + " and one variable", size_hint=(0.8, 1))
            close = Button(text="Close", size_hint=(0.2, 1))
            close.bind(on_press=error.dismiss)
            content.add_widget(lab)
            content.add_widget(close)
            error.open()

    def get_all_z_inline_chain(self):
        """
        Gather data over all z values for current variable when inline chain tool was used. Assumes only one variable
        and only one chain are selected.

        Returns:
            3D Array of concatenated transect data over all z values in the NetCDF file.
        """
        v = self.active_data[self.active_vars[0]]
        z = v[next(iter(v))]
        chain = next(iter(z))
        width = 0
        for tran in list(z[chain].keys()):
            width += len(z[chain][tran]['Cut'])
        chain_points = copy.copy(self.all_transects[chain])
        # Determine the boundary points to subset around chain
        bound_points = copy.copy(chain_points["Cut 1"])
        for seg in list(chain_points.keys())[2:]:
            arr = copy.copy(chain_points[seg])
            xs_ys = [[arr[0], arr[2]], [arr[1], arr[3]]]
            for n, c in enumerate(xs_ys):
                for i in c:
                    if i < bound_points[0 + n]:
                        bound_points[0 + n] = i
                    elif i > bound_points[2 + n]:
                        bound_points[2 + n] = i
        # Subset around chain
        ds = self.config[self.f_type]['data']
        z_len = len(ds.coords[self.config[self.f_type]['z']].data)
        f_config = copy.copy(self.config)
        config = f_config[self.f_type]
        config['var'] = self.active_vars[0]
        ds = ds[config['var']].rename({config['y']: "y", config['x']: "x", config['z']: "z"})

        x_points = np.sort(np.array([bound_points[0], bound_points[2]]))
        y_points = np.sort(np.array([bound_points[1], bound_points[3]]))

        if ds["x"][1] < ds["x"][0]:
            og_x = ds["x"][::-1]
        else:
            og_x = ds["x"]

        if ds["y"][1] < ds["y"][0]:
            og_y = ds["y"][::-1]
        else:
            og_y = ds["y"]

        # Create new, equidistant coordinate arrays
        x_pix = min(abs(og_x.data[:-1] - og_x.data[1:]))
        y_pix = min(abs(og_y.data[:-1] - og_y.data[1:]))

        curr_x = np.arange(og_x.min(), og_x.max() + x_pix, x_pix)
        curr_y = np.arange(og_y.min(), og_y.max() + y_pix, y_pix)

        x_vals = x_points * x_pix + curr_x.min()
        y_vals = y_points * y_pix + curr_y.min()

        sub_x = og_x[np.searchsorted(og_x, x_vals[0]) - 1:np.searchsorted(og_x, x_vals[1]) + 1]
        new_x = np.arange(sub_x[0], sub_x[-1] + x_pix, x_pix)
        sub_y = og_y[np.searchsorted(og_y, y_vals[0]) - 1:np.searchsorted(og_y, y_vals[1]) + 1]
        new_y = np.arange(sub_y[0], sub_y[-1] + y_pix, y_pix)

        sub_data = ds.sel({"x": sub_x, "y": sub_y})
        sub_data = sub_data.transpose("y", "x", "z")
        sub_data['z'] = sub_data['z'].astype(str)
        sub_data = sub_data.data
        if ds["z"][1] < ds["z"][0]:
            sub_data = np.flip(sub_data, 2)
        coord_scales = [curr_x.min(), curr_y.min(), curr_x.min(), curr_y.min()]
        sub_scales = [new_x.min(), new_y.min(), new_x.min(), new_y.min()]
        pix_scales = [x_pix, y_pix, x_pix, y_pix]

        # Array of data values at x, y pairs for each z
        all_z = np.empty(shape=(z_len, width))
        for z in range(0, z_len):
            # Get transect data for each z level and add to array
            interpolator = RegularGridInterpolator((sub_y, sub_x), sub_data[:, :, z], method="linear",
                                                   bounds_error=False, fill_value=None)
            X, Y = np.meshgrid(new_x, new_y)
            interp_data = interpolator((Y, X))
            s_points = ((np.array(chain_points["Cut 1"]) * pix_scales) + coord_scales - sub_scales) / pix_scales
            dat = func.ip_get_points(s_points, interp_data, f_config)["Cut"]
            for tran in list(chain_points.keys())[3:]:
                s_points = ((np.array(chain_points[tran]) * pix_scales) + coord_scales - sub_scales) / pix_scales
                res = func.ip_get_points(s_points, interp_data, f_config)["Cut"]

                dat = np.concatenate((dat, res))
            all_z[z, :] = dat
        return all_z

    def get_all_z_orthogonal_chain(self):
        """
        Gather transect data over all z values for current variable. Assumes only one variable and only one transect are
        selected.

        Returns:
            3D Array of transect data over all z values in the NetCDF file
        """
        # Get transect coordinates
        v = self.active_data[self.active_vars[0]]
        z = v[next(iter(v))]
        group = next(iter(z))
        tran = next(iter(z[group]))
        points = self.all_transects[group][tran]
        width = len(z[group][tran]['Cut'])
        ds = self.config[self.f_type]['data']

        # Subset dataset around transect and convert coordinates
        z_len = len(ds.coords[self.config[self.f_type]['z']].data)
        f_config = copy.copy(self.config)
        config = f_config[self.f_type]
        config['var'] = self.active_vars[0]
        ds = ds[config['var']].rename({config['y']: "y", config['x']: "x", config['z']: "z"})

        x_points = np.sort(np.array([points[0], points[2]]))
        y_points = np.sort(np.array([points[1], points[3]]))

        if ds["x"][1] < ds["x"][0]:
            og_x = ds["x"][::-1]
        else:
            og_x = ds["x"]

        if ds["y"][1] < ds["y"][0]:
            og_y = ds["y"][::-1]
        else:
            og_y = ds["y"]
        x_pix = min(abs(ds["x"].data[:-1] - ds["x"].data[1:]))
        y_pix = min(abs(ds["y"].data[:-1] - ds["y"].data[1:]))
        curr_x = np.arange(ds["x"].min(), ds["x"].max() + x_pix, x_pix)
        curr_y = np.arange(ds["y"].min(), ds["y"].max() + y_pix, y_pix)

        x_vals = x_points + curr_x.min()
        y_vals = y_points + curr_y.min()

        sub_x = og_x[np.searchsorted(og_x, x_vals[0]) - 1:np.searchsorted(og_x, x_vals[1]) + 1]
        new_x = np.arange(sub_x[0], sub_x[-1] + x_pix, x_pix)
        sub_y = og_y[np.searchsorted(og_y, y_vals[0]) - 1:np.searchsorted(og_y, y_vals[1]) + 1]
        new_y = np.arange(sub_y[0], sub_y[-1] + y_pix, y_pix)

        sub_data = ds.sel({"x": sub_x, "y": sub_y})
        sub_data = sub_data.transpose("y", "x", "z")
        sub_data['z'] = sub_data['z'].astype(str)
        sub_data = sub_data.data
        if ds["z"][1] < ds["z"][0]:
            sub_data = np.flip(sub_data, 2)

        coord_scales = [curr_x.min(), curr_y.min(), curr_x.min(), curr_y.min()]
        sub_scales = [new_x.min(), new_y.min(), new_x.min(), new_y.min()]
        pix_scales = [x_pix, y_pix, x_pix, y_pix]

        new_points = (np.array(points) * pix_scales + coord_scales - sub_scales) / pix_scales

        # Array of data values at x, y pairs for each z
        all_z = np.empty(shape=(z_len, width))
        for z in range(0, z_len):
            # Get transect data for each z level and add to array
            interpolator = RegularGridInterpolator((sub_y, sub_x), sub_data[:, :, z], method="linear",
                                                   bounds_error=False, fill_value=None)
            X, Y = np.meshgrid(new_x, new_y)
            interp_data = interpolator((Y, X))
            dat = func.ip_get_points(new_points, interp_data, f_config)
            all_z[z, :] = dat["Cut"]
        return all_z

    def plot_active(self):
        """
        Creates figure of plots of currently selected data

        Returns:
            Final completed figure
        """
        # Determine subplot layout based on the number of active variables selected
        num = len(self.active_vars)
        if num <= 1:
            col = 1
            row = 1
        else:
            col = 2
            if num % 2 == 0:
                row = int(num / 2)
            else:
                row = int((num + 1) / 2)
        fig, ax = plt.subplots(row, col)

        if self.f_type == "image":  # If image just plot
            names = self.plot_single(self.active_data, ax, "Mean RGB Value")
        else:
            count = 0
            for var in self.active_vars:
                # Subplot for each variable
                count += 1
                if count % 2 == 0:
                    c = 1
                    r = int((count / 2) - 1)
                else:
                    c = 0
                    r = int(((count + 1) / 2) - 1)
                if row == 1 and col == 1:
                    names = self.plot_single(self.active_data[var], ax, var)
                elif row == 1:
                    names = self.plot_single(self.active_data[var], ax[c], var)
                else:
                    names = self.plot_single(self.active_data[var], ax[r, c], var)
            if len(self.active_vars) % 2 == 1 and len(self.active_vars) > 1:
                # If unused subplot in layout, delete it
                plt.delaxes(ax[r, 1])
        fig.legend(names, title="Legend", bbox_to_anchor=(1, 1))
        return fig

    def plot_single(self, data, ax, label):
        """
        Creates a single plot of selected chain/transect data for a single variable (if NetCDF)

        Args:
            data: Currently selected chain/transect data. Either self.active_data itself or a sub-dictionary
            ax: Plot axis on which to make plot
            label: Label for the y axis of plot. If NetCDF use variable if Image use 'Mean RGB Value'

        Returns:
            List of string labels for the plot's legend
        """
        # Create a non-nested dictionary of selections with appropriate labels
        dat = copy.copy(data)
        plot_dat = {}

        if list(dat.keys())[0][0:10] != "Orthogonal" and list(dat.keys())[0][0:6] != "Inline":
            # Gather data for all transects selected across all groups for all Z levels selected
            for z in list(dat.keys()):
                if len(z) >= 12:
                    z_name = z[:12] + "..."
                else:
                    z_name = z
                plot_dat = self.plot_gather_data(dat[z], "Z: " + z_name + " ", plot_dat)
        else:
            # Gather data for all transects selected across all groups
            plot_dat = self.plot_gather_data(dat, "", plot_dat)

        # Plot data by turning dictionary into a data frame
        df = pd.DataFrame.from_dict(dict([(k, pd.Series(v)) for k, v in plot_dat.items()]))
        x = np.asarray(df.index)
        axis = (x - x[0]) / (x[-1] - x[0])
        ax.plot(axis, df)

        ax.set_ylabel(label.capitalize())
        if not self.f_type == "netcdf":
            ax.set_ylim(ymin=0)
        if self.t_type == "Orthogonal":
            x_text = "Normalized Long Transect Distance"
        elif self.t_type == "Inline":
            x_text = "Normalized Long Chain Distance"
        ax.set_xlabel(x_text)
        plt.tight_layout()
        # Return dataframe column names for legend
        return df.columns

    def plot_gather_data(self, dat, name_start, plot_dat):
        """
        Iterates group transect data and gathers it into a dictionary for plotting. If tool used is inline chain,
        ensures that transect data is in direction user clicked the points (left to right or right to left).

        Args:
            dat (dict): Dictionary of all chains or all transect data that are selected for plotting
            name_start (str): Start of string to use as key name for plotting dictionary. Key names are ultimately used
                for labels in plot legend. 'Z: <z_value>' if 3D NetCDF data, otherwise just ''.
            plot_dat: Plotting dictionary to add data to

        Returns:
            Plotting dictionary with chain/transect data added in the correct plotting format
        """
        for obj in list(dat.keys()):
            if obj[0:6] == "Inline":
                title = name_start + "C" + obj[-1]
                all_trans = np.array(dat[obj]["Cut 1"]["Cut"])
                for tran in list(dat[obj].keys())[1:]:
                    n_dat = np.array(dat[obj][tran]["Cut"])
                    all_trans = np.concatenate((all_trans, n_dat))
                plot_dat[title] = all_trans
            else:
                title = name_start + "C" + obj[-1] + " "
                for tran in list(dat[obj].keys()):
                    if tran == "Average":
                        plot_dat[title + tran] = dat[obj][tran]
                    else:
                        plot_dat[title + tran] = dat[obj][tran]["Cut"]
        return plot_dat

    def update_plot(self):
        """
        Remakes and replaces plot based on current selections.
        """
        self.ids.plotting.remove_widget(self.plot)
        self.plot_active()
        temp = io.BytesIO()
        plt.savefig(temp, format="png")
        temp.seek(0)
        plt.close()
        self.plot = ui.image.Image(source="", texture=CoreImage(io.BytesIO(temp.read()), ext="png").texture,
                                   size_hint=(0.7, 1), fit_mode="contain")
        self.ids.plotting.add_widget(self.plot, len(self.ids.plotting.children))

    def get_data(self):
        """
        Gathers transect data for currently selected variables, z values, and transects.

        Returns:
            Nested dictionary of transect data with hierarchy:
                Variables -> Z values -> Groups -> Transects -> X,Y, Cut
            If only 2D NetCDF file there is no Z values level. If an image there is no Variables or Z Values level.
        """
        # Get transect data for list of active transect points
        config = copy.copy(self.config[self.f_type])
        values = {}
        if len(self.active_vars) >= 1:
            # If data has variables
            for var in self.active_vars:
                values[var] = {}
                config["var"] = var
                if len(self.active_z) >= 1:
                    # If data has multiple Z levels
                    for z in self.active_z:
                        # Multiple Z selection
                        values[var][z] = {}
                        config["z_val"] = z
                        values[var][z] = self.get_transect_data(config)
                else:
                    values[var] = self.get_transect_data(config)
        else:
            values = self.get_transect_data(config)
        return values

    def get_transect_data(self, config):
        """
        Iterates through the active transect points and returns the transect data.

        Args:
            config: Either a Dataset (NetCDF) or a 2D array (Image) to take transect data from

        Return:
            Returns dictionary of nested tool group dictionaries of transect data
        """
        val_dict = {}
        for key in list(self.active_transects.keys()):
            # All groups selected
            val_dict[key] = {}
            for tran in list(self.active_transects[key].keys()):
                if self.active_transects[key][tran]:
                    # All transects selected
                    if tran == "Average":
                        val_dict[key][tran] = self.get_average(key, config)
                    else:
                        sub_d, sub_p, scales = func.subset_around_transect(config, self.all_transects[key][tran])
                        if self.f_type == "image":
                            x_lab = "x"
                            y_lab = "y"
                        else:
                            x_lab = self.config[self.f_type]["x"]
                            y_lab = self.config[self.f_type]["y"]
                        val_dict[key][tran] = func.ip_get_points(sub_p, sub_d, self.config)
                        val_dict[key][tran][x_lab] = [x + scales[0] for x in val_dict[key][tran][x_lab]]
                        val_dict[key][tran][y_lab] = [y + scales[1] for y in val_dict[key][tran][y_lab]]

            if len(val_dict[key]) == 0:
                val_dict.pop(key)
        return val_dict

    def get_average(self, key, config):
        """
        Finds average of all transects in an orthogonal chain. Orthogonal transect width must be the same for the
        entire chain.

        Args:
            key (str): 'Orthogonal Chain #'
            config: 2D array, currently loaded dataset

        Returns:
            1D array of length of transect width containing average transect values for the orthogonal chain.
        """
        dat = np.zeros(self.all_transects[key]['Width'][0])
        for tran in list(self.all_transects[key].keys())[3:]:
            sub_d, sub_p, scales = func.subset_around_transect(config, self.all_transects[key][tran])
            dat += func.ip_get_points(sub_p, sub_d, self.config)['Cut']
        dat = dat / len(list(self.all_transects[key].keys())[3:])
        return list(dat)
