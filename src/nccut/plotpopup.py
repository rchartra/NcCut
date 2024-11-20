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
from plyer import filechooser
import nccut.functions as func
from nccut.plotwindow import PlotWindow
from kivy.core.image import Image as CoreImage
import matplotlib.pyplot as plt
from PIL import Image as im
import numpy as np
import copy
import pandas as pd
import datetime
import json
import pathlib
import os


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
        t_type (str): 'Marker' if transects came from transect marker tool or 'Chain' if transects came from transect
            chain tool
        active_transects (dict): Dictionary of currently selected transects. 'Click <X Cord>', 'Click <Y Cord>', and
            'Width' fields should be removed (if marker tool) to simplify plotting. Contains average
            of transects if marker tool was used with a constant transect width.
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
        if list(self.all_transects.keys())[0][0:-2] == "Marker":
            self.t_type = "Marker"
        elif list(self.all_transects.keys())[0][0:-2] == "Chain":
            self.t_type = "Chain"

        # Create nested dictionary of Booleans indicating which transects are currently selected
        self.active_transects = {}

        act = copy.deepcopy(self.all_transects)
        for key in list(act.keys()):
            self.active_transects[key] = {}
            # Remove fields that don't get plotted
            if self.t_type == "Marker":
                for k in list(act[key].keys())[:3]:
                    act[key].pop(k)
            elif self.t_type == "Chain":
                for k in list(act[key].keys())[:2]:
                    act[key].pop(k)
            self.active_transects[key] = dict.fromkeys(act[key], False)

            # If marker and all values same width, add an average option
            if self.t_type == "Marker":
                w_lis = self.all_transects[key]['Width']
                if all(x == w_lis[0] for x in w_lis):
                    new = {"Average": False}
                    new.update(self.active_transects[key])
                    self.active_transects[key] = new

        # Start with the first group selected
        first = list(self.active_transects.keys())[0]
        self.active_transects[first] = dict.fromkeys(self.active_transects[first], True)

        # If marker start with average not selected
        if self.t_type == "Marker":
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
        if self.t_type == "Marker":
            self.t_drop = self.get_marker_dropdown()
        elif self.t_type == "Chain":
            self.t_drop = self.get_chain_dropdown()
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

                # Plot All Z option
                zp_box = ui.boxlayout.BoxLayout(size_hint=(1, None), height=self.b_height, padding=dp(10))
                zp_btn = func.RoundedButton(text="Plot all Z as Img", size_hint=(1, 1), font_size=self.font)
                zp_btn.bind(on_press=lambda x: self.get_all_z_plot())
                zp_box.add_widget(zp_btn)
                self.ids.sidebar.add_widget(zp_box, 1)

                # Export All Z Option
                self.allz_btn = func.RoundedButton(text="All Z Data", size_hint_x=None, width=dp(50) + self.font * 3,
                                                   font_size=self.font)
                self.allz_btn.bind(on_press=lambda x: self.file_input('all_z'))
                self.ids.buttons.add_widget(self.allz_btn)
                self.widgets_with_text.extend([z_lab, self.z_select, zp_btn])
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
        fpath = filechooser.save_file(filters=f_types)
        if fpath is not None and len(fpath) > 0:
            fpath = fpath[0]
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
        Adds back fields removed for plotting purposes if marker or chain tool was used

        Args:
            dicti (dict): Dictionary of transect data from a single group

        Returns:
            Dictionary of transect data with non-plotted data fields added back in.
        """
        if list(dicti.keys())[0][0:6] == "Marker":
            for marker in list(dicti.keys()):
                for key in list(self.all_transects[marker].keys())[:3]:
                    dicti[marker][key] = list(self.all_transects[marker][key])
        elif list(dicti.keys())[0][0:5] == "Chain":
            for chain in list(dicti.keys()):
                for key in list(self.all_transects[chain].keys())[:2]:
                    dicti[chain][key] = list(self.all_transects[chain][key])
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

    def get_chain_dropdown(self):
        """
        Build dropdown menu for selecting chains.

        Returns:
            :class:`nccut.plotpopup.BackgroundDropDown` for transect options
        """
        # Get dropdown for transect options
        drop = BackgroundDropDown(auto_width=False, width=dp(180), max_height=dp(200))
        all_box = ui.boxlayout.BoxLayout(spacing=dp(10), padding=dp(10), size_hint_y=None, height=dp(30) + self.font)
        drop.add_widget(all_box)
        all_btn = func.RoundedButton(text="Select All", font_size=self.font)
        for i in list(self.active_transects.keys()):
            c_box = ui.boxlayout.BoxLayout(spacing=dp(5), size_hint_y=None, height=dp(30) + self.font)
            but = Button(text=i, size_hint=(0.5, 1), background_color=[0, 0, 0, 0], font_size=self.font)
            check = CheckBox(active=all(self.active_transects[i].values()), size_hint=(0.5, 1))
            check.bind(active=lambda x, y, t=i: self.on_chain_checkbox(x, t))
            but.bind(on_press=lambda x, c=check: self.on_check_button(c))
            c_box.add_widget(but)
            c_box.add_widget(check)
            drop.add_widget(c_box)
        all_btn.bind(on_press=lambda x: self.select_all(drop.children[0].children[:-1]))
        all_box.add_widget(all_btn)
        return drop

    def on_chain_checkbox(self, check, chain, *args):
        """
        Updates plot when a chain checkbox is clicked. Safeguards so at least one chain
        is always selected.

        Args:
            check: Reference to kivy.uix.checkbox.CheckBox in transect list
            chain (str): Name of chain 'Chain #'
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

    def get_marker_dropdown(self):
        """
        Build dropdown menu for Markers with sub-menus for the individual transects.

        Returns:
            :class:`nccut.plotpopup.BackgroundDropDown` for Marker options
        """
        # Get dropdown for marker options
        marker_list = BackgroundDropDown(auto_width=False, width=dp(180), max_height=dp(300))
        for i in list(self.all_transects.keys()):
            g_box = ui.boxlayout.BoxLayout(spacing=dp(10), padding=dp(10), size_hint_y=None, height=dp(30) + self.font,
                                           width=dp(180))
            btn = func.RoundedButton(text=i, font_size=self.font)
            btn.bind(on_press=lambda but=btn, txt=i: self.transect_drop(txt, but))
            g_box.add_widget(btn)
            marker_list.add_widget(g_box)
        return marker_list

    def transect_drop(self, marker, button):
        """
        Attaches transect dropdowns to marker buttons in marker dropdown menu

        Args:
            marker (str): Marker label. Ex: 'Marker #'
            button: RoundedButton, Marker's button in marker dropdown menu
        """
        temp_transect_drop = self.get_transect_dropdown(marker)
        temp_transect_drop.open(button)

    def get_transect_dropdown(self, key):
        """
        Build dropdown menu for selecting transects from a marker.

        Args:
            key (str): Name of marker selecting from. Ex: 'Marker #'

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
        If all checkboxes are checked, uncheck all boxes. Otherwise check all boxes. If a box is the only box checked
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

    def on_transect_checkbox(self, check, marker, transect, *args):
        """
        Updates plot when a transect checkbox is clicked. Safeguards so at least one transect
        is always selected.

        Args:
            check: Reference to kivy.uix.checkbox.CheckBox in transect list
            marker (str): Name of marker selecting from. Ex: 'Marker #'
            transect (str): Name of transect 'Cut #'
        """
        # Select or deselect transect
        self.active_transects[marker][transect] = not self.active_transects[marker][transect]

        # Check this isn't the last transect selected
        count = 0
        for key in list(self.active_transects.keys()):  # Count current transects
            count += sum(self.active_transects[key].values())
        if count == 0:  # If last transect unchecked, recheck and ignore
            self.active_transects[marker][transect] = not self.active_transects[marker][transect]
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
        if self.t_type == "Marker":
            t_count = 0
            for key in list(self.active_transects.keys()):
                # Count current transects selected
                no_avg = copy.copy(self.active_transects[key])
                no_avg.pop("Average")
                t_count += sum(no_avg.values())
            if t_count == 1 and len(self.active_vars) == 1:
                plot_ok = True
        elif self.t_type == "Chain":
            c_count = 0
            for key in list(self.active_transects.keys()):
                # Count current transects selected
                c_count += all(self.active_transects[key].values())
            if c_count == 1 and len(self.active_vars) == 1:
                plot_ok = True
        if plot_ok:
            # Go ahead and plot
            self.ids.plotting.remove_widget(self.plot)
            if self.t_type == "Marker":
                z_data = self.get_all_z_marker()
            elif self.t_type == "Chain":
                z_data = self.get_all_z_chain()
            self.plot = PlotWindow(self.config[self.f_type], z_data, self.home.display.colormap, size_hint=(0.7, 1))
            self.plot.bind(size=self.plot.load)
            self.ids.plotting.add_widget(self.plot, len(self.ids.plotting.children))
        else:
            # Error popup if more than one transect and/or variable is selected
            content = ui.boxlayout.BoxLayout()
            error = Popup(title="Error", content=content, size_hint=(0.5, 0.15))
            if self.t_type == "Marker":
                text = "transect"
            elif self.t_type == "Chain":
                text = "chain"
            lab = Label(text="Please only select one " + text + " and one variable", size_hint=(0.8, 1))
            close = Button(text="Close", size_hint=(0.2, 1))
            close.bind(on_press=error.dismiss)
            content.add_widget(lab)
            content.add_widget(close)
            error.open()

    def get_all_z_chain(self):
        """
        Gather data over all z values for current variable when chain tool used. Assumes only one variable and only one
        chain are selected.

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
        data, scaled_bound_points, scales = func.subset_around_transect(ds, bound_points)
        point_scales = np.array(bound_points) - np.array(scaled_bound_points)
        data = data.transpose('y', 'x', 'z')
        data['z'] = data['z'].astype(str)
        data = np.flip(data.data, 0)

        # Array of data values at x, y pairs for each z
        all_z = np.empty(shape=(z_len, width))
        for d in range(0, z_len):
            # Get transect data for each z level and add to array
            curr = data[:, :, d]
            s_points = np.array(chain_points["Cut 1"]) - point_scales
            dat = func.ip_get_points(s_points, curr, f_config)["Cut"]
            for tran in list(chain_points.keys())[3:]:
                s_points = np.array(chain_points[tran]) - point_scales
                res = func.ip_get_points(s_points, curr, f_config)["Cut"]
                dat = np.concatenate((dat, res))
            all_z[d, :] = dat
        return all_z

    def get_all_z_marker(self):
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

        # Subset dataset around transect
        z_len = len(ds.coords[self.config[self.f_type]['z']].data)
        f_config = copy.copy(self.config)
        config = f_config[self.f_type]
        config['var'] = self.active_vars[0]
        ds = ds[config['var']].rename({config['y']: "y", config['x']: "x", config['z']: "z"})
        data, scale_points, scales = func.subset_around_transect(ds, points)
        data = data.transpose('y', 'x', 'z')
        data['z'] = data['z'].astype(str)
        data = np.flip(data.data, 0)

        # Array of data values at x, y pairs for each z
        all_z = np.empty(shape=(z_len, width))
        for d in range(0, z_len):
            # Get transect data for each z level and add to array
            curr = data[:, :, d]
            dat = func.ip_get_points(scale_points, curr, f_config)
            all_z[d, :] = dat['Cut']
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

        if list(dat.keys())[0][0:6] != "Marker" and list(dat.keys())[0][0:5] != "Chain":
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
        if self.t_type == "Marker":
            x_text = "Normalized Long Transect Distance"
        elif self.t_type == "Chain":
            x_text = "Normalized Long Chain Distance"
        ax.set_xlabel(x_text)
        plt.tight_layout()
        # Return dataframe column names for legend
        return df.columns

    def plot_gather_data(self, dat, name_start, plot_dat):
        """
        Iterates group transect data and gathers it into a dictionary for plotting. If tool used is chain, ensures that
        transect data is in direction user clicked the points (left to right or right to left).

        Args:
            dat (dict): Dictionary of all chains or all markers transect data that are selected for plotting
            name_start (str): Start of string to use as key name for plotting dictionary. Key names are ultimately used
                for labels in plot legend. 'Z: <z_value>' if 3D NetCDF data, otherwise just ''.
            plot_dat: Plotting dictionary to add data to

        Returns:
            Plotting dictionary with chain/marker data added in the correct plotting format
        """
        for obj in list(dat.keys()):
            if obj[0:5] == "Chain":
                title = name_start + "C" + obj[-1]
                all_trans = np.array(dat[obj]["Cut 1"]["Cut"])
                for tran in list(dat[obj].keys())[1:]:
                    n_dat = np.array(dat[obj][tran]["Cut"])
                    all_trans = np.concatenate((all_trans, n_dat))
                plot_dat[title] = all_trans
            else:
                title = name_start + "M" + obj[-1] + " "
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
                        curr = func.sel_data(config)
                        values[var][z] = self.get_transect_data(curr)
                else:
                    curr = func.sel_data(config)
                    values[var] = self.get_transect_data(curr)

        else:
            curr = np.asarray(im.open(config))
            values = self.get_transect_data(curr)
        return values

    def get_transect_data(self, curr):
        """
        Iterates through the active transect points and returns the transect data.

        Args:
            curr: Either a Dataset (NetCDF) or a 2D array (Image) to take transect data from

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
                        val_dict[key][tran] = self.get_average(key, curr)
                    else:
                        sub_d, sub_p, scales = func.subset_around_transect(curr, self.all_transects[key][tran])
                        if self.f_type == "image":
                            x_lab = "x"
                            y_lab = "y"
                            dat = sub_d
                        else:
                            x_lab = self.config[self.f_type]["x"]
                            y_lab = self.config[self.f_type]["y"]
                            dat = np.flip(sub_d.data, 0)
                        val_dict[key][tran] = func.ip_get_points(sub_p, dat, self.config)
                        val_dict[key][tran][x_lab] = [x + scales[1] for x in val_dict[key][tran][x_lab]]
                        val_dict[key][tran][y_lab] = [x + scales[0] for x in val_dict[key][tran][y_lab]]

            if len(val_dict[key]) == 0:
                val_dict.pop(key)
        return val_dict

    def get_average(self, key, curr):
        """
        Finds average of all transects in a marker. Transect width must be the same for the entire marker.

        Args:
            key (str): 'Marker #'
            curr: 2D array, currently loaded dataset

        Returns:
            1D array of length of transect width containing average transect values for the marker.
        """
        dat = np.zeros(self.all_transects[key]['Width'][0])
        for tran in list(self.all_transects[key].keys())[3:]:
            sub_d, sub_p, scales = func.subset_around_transect(curr, self.all_transects[key][tran])
            if self.f_type == "image":
                data = sub_d
            else:
                data = np.flip(sub_d.data, 0)
            dat += func.ip_get_points(sub_p, data, self.config)['Cut']
        dat = dat / len(list(self.all_transects[key].keys())[3:])
        return list(dat)
