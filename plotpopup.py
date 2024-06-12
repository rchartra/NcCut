"""
UI and functionality for plotting and saving popup.

Creates UI elements of the popup and manages the creation of plots based on user input.
Manages the saving of the plots and user selected data.
"""

import io
import kivy.uix as ui
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.uix.dropdown import DropDown
import functions as func
from kivy.core.image import Image as CoreImage
import matplotlib.pyplot as plt
import numpy as np
import copy
import pandas as pd
import json
import cv2
import img2pdf


class BackgroundDropDown(DropDown):
    """
    General class for a dropdown menu with a background color

    Attributes:
        rect: Rectangle object that serves as background to the dropdown.

        Inherits additional attributes from kivy.uix.dropdown.Dropdown (see kivy docs)
    """
    def open(self, widget):
        """
        Overwrites DropDown open method to also draw a background rectangle.

        Args:
            widget: RoundedButton to which dropdown is bound
        """
        super(BackgroundDropDown, self).open(widget)
        with self.canvas.before:
            Color(rgb=[0.2, 0.2, 0.2])
            self.rect = Rectangle(size=self.size, pos=self.pos, radius=[10, ])
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
        home: Reference to root HomeScreen instance.
        all_transects: Dictionary of data from all transects marked out by the user.
        t_type: String: 'Marker' if transects came from transect marker tool or 'Multi' if transects
            came from transect tool.
        active_transects: Dictionary of currently selected transects. 'Click X', 'Click Y', and
            'Width' fields should be removed (if marker tool) to simplify plotting. Contains average
            of transects if marker tool was used with a constant transect width.
        f_type: String, If file is NetCDF file: 'NC' if only 2 dimensions, 'NC_Z' if 3 dimensions. If
            file is a JPG or PNG: 'Img'.
        active_z: List of selected Z values. Empty list if 2D NetCDF or Image file.
        active_vars: List of selected variables. Empty list if image file.
        plot: Image containing plot.
        plotting: BoxLayout that holds plot and selection sidebar.
        title: String, popup title
        content: BoxLayout containing all UI elements in popup
        size_hint: Tuple (width, height) of relative size of popup to window
        t_select: RoundedButton which opens transect selection dropdown menu
        v_select: RoundedButton which opens variable selection dropdown menu (Only if NetCDF file)
        z_select: RoundedButton which opens z value selection dropdown menu (Only if 3D NetCDF file)

        Inherits additional attributes from kivy.uix.popup.Popup (see kivy docs)
    """
    def __init__(self, transects, home, **kwargs):
        """
        Defines popup UI elements and opens popup.

        Args:
            transects: Dictionary of transect data from tool which opened popup
            home: Reference to root HomeScreen instance.
        """
        super(PlotPopup, self).__init__(**kwargs)
        self.home = home
        self.all_transects = transects
        if list(self.all_transects.keys())[0][0:-2] == "Marker":
            self.t_type = "Marker"
        else:
            self.t_type = "Multi"

        # Create nested dictionary of Booleans indicating which transects are currently selected
        self.active_transects = {}

        act = copy.deepcopy(self.all_transects)
        for key in list(act.keys()):
            self.active_transects[key] = {}
            if self.t_type == "Marker":  # Remove fields that don't get plotted
                act[key].pop("Click X")
                act[key].pop("Click Y")
                act[key].pop("Width")
            self.active_transects[key] = dict.fromkeys(act[key], False)

            # If marker and all values same width, add an average option
            if self.t_type == "Marker":
                w_lis = self.all_transects[key]['Width']
                if all(x == w_lis[0] for x in w_lis):
                    new = {"Average": False}
                    new.update(self.active_transects[key])
                    self.active_transects[key] = new

        # If not marker, start will all transects selected
        first = list(self.active_transects.keys())[0]
        self.active_transects[first] = dict.fromkeys(self.active_transects[first], True)

        # If marker start with first marker selected
        if self.t_type == "Marker":
            w_lis = self.all_transects[first]['Width']
            if all(x == w_lis[0] for x in w_lis):
                self.active_transects[first]["Average"] = False

        # Initialize dropdown selections
        if self.home.nc:
            if self.home.netcdf['z'] == "Select...":
                self.f_type = "NC"
                self.active_z = []
            else:
                self.f_type = "NC_Z"
                self.active_z = [self.home.netcdf['z_val']]
            self.active_vars = [self.home.netcdf["var"]]
        else:
            self.f_type = "Img"
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

        self.plot = ui.image.Image(source="", texture=CoreImage(io.BytesIO(temp.read()), ext="png").texture,
                                   size_hint=(0.7, 1))
        # Plot
        self.plotting = ui.boxlayout.BoxLayout(spacing=dp(20), size_hint=(1, 0.9))
        self.plotting.add_widget(self.plot)
        self.title = "Plot Transects"
        self.content = ui.boxlayout.BoxLayout(orientation='vertical', spacing=dp(20), padding=dp(20))
        self.size_hint = (0.8, 0.8)
        sidebar = ui.boxlayout.BoxLayout(orientation='vertical', size_hint=(0.3, 1), padding=dp(10), spacing=dp(20))

        # Saving Data/Plotting buttons

        buttons = ui.boxlayout.BoxLayout(orientation='horizontal', size_hint=(1, .1), spacing=dp(10))

        data_btn = func.RoundedButton(text="Save Selected Data", size_hint=(.2, 1), font_size=self.home.font)
        data_btn.bind(on_press=lambda x: self.file_input('data'))

        png_btn = func.RoundedButton(text='Save Plot to PNG', size_hint=(.2, 1), font_size=self.home.font)
        png_btn.bind(on_press=lambda x: self.file_input('png'))

        pdf_btn = func.RoundedButton(text='Save Plot to PDF', size_hint=(.2, 1), font_size=self.home.font)
        pdf_btn.bind(on_press=lambda x: self.file_input('pdf'))

        buttons.add_widget(data_btn)
        buttons.add_widget(png_btn)
        buttons.add_widget(pdf_btn)

        # Transect selection
        t_box = ui.boxlayout.BoxLayout(size_hint=(1, 0.2), spacing=dp(30))
        lab = Label(text="Select Transects: ", size_hint=(0.3, 1), font_size=self.home.font)
        t_box.add_widget(lab)
        self.t_select = func.RoundedButton(text="Select...", size_hint=(0.7, 1), font_size=self.home.font)
        t_box.add_widget(self.t_select)
        if self.t_type == "Marker":
            t_drop = self.get_marker_dropdown()
        else:
            t_drop = self.get_cut_dropdown('Multi')
        self.t_select.bind(on_press=lambda x: t_drop.open(self.t_select))
        sidebar.add_widget(t_box)

        if self.home.nc:
            # Variable Selection
            v_box = ui.boxlayout.BoxLayout(size_hint=(1, 0.2), spacing=dp(30))
            v_box.add_widget(Label(text="Select Variables: ", size_hint=(0.3, 1), font_size=self.home.font))
            self.v_select = func.RoundedButton(text="Select...", size_hint=(0.7, 1),
                                               font_size=self.home.font)
            v_box.add_widget(self.v_select)
            v_drop = self.get_var_dropdown()
            self.v_select.bind(on_press=lambda x: v_drop.open(self.v_select))
            sidebar.add_widget(v_box)
            if self.home.netcdf['z'] != "Select...":
                # Z Selection
                z_box = ui.boxlayout.BoxLayout(size_hint=(1, 0.2), spacing=dp(30))
                z_box.add_widget(Label(text="Select Z Values: ", size_hint=(0.3, 1), font_size=self.home.font))
                self.z_select = func.RoundedButton(text="Select...", size_hint=(0.7, 1),
                                                   font_size=self.home.font)
                z_box.add_widget(self.z_select)
                z_drop = self.get_z_dropdown()
                self.z_select.bind(on_press=lambda x: z_drop.open(self.z_select))
                sidebar.add_widget(z_box)

                # All Z option
                zp_box = ui.boxlayout.BoxLayout(size_hint=(1, 0.2), spacing=dp(30))
                zp_btn = func.RoundedButton(text="Plot all Z as Img", font_size=self.home.font)
                zp_btn.bind(on_press=lambda x: self.get_all_z_plot())
                zp_box.add_widget(zp_btn)
                sidebar.add_widget(zp_box)

                allz_btn = func.RoundedButton(text="Save All Z Data", size_hint=(.2, 1), font_size=self.home.font)
                allz_btn.bind(on_press=lambda x: self.file_input('all_z'))
                buttons.add_widget(allz_btn)
            else:
                # Spacer if 2D NetCDF
                sidebar.add_widget(Label(text="", size_hint=(1, 0.6)))
        else:
            # Spacer if Image
            sidebar.add_widget(Label(text="", size_hint=(1, 0.8)))

        self.plotting.add_widget(sidebar)
        self.content.add_widget(self.plotting)

        close = func.RoundedButton(text="Close", size_hint=(.2, 1))
        close.bind(on_press=self.dismiss)
        buttons.add_widget(close)
        self.content.add_widget(buttons)
        self.open()

    def file_input(self, type):
        """
        Popup window for user to give name for plot/json file to be saved.

        Args:
            type: String corresponding to what is being saved:
                'data': Transect data for selections
                'all_z_data': Transect data for selections for all z dimension values
                'png': Current plot as a PNG file
                'pdf': Current plot as a PDF file
        """
        content = ui.boxlayout.BoxLayout(orientation='horizontal')
        popup = Popup(title="File Name", content=content, size_hint=(0.5, 0.15))
        txt = TextInput(size_hint=(0.7, 1), hint_text="Enter File Name")
        content.add_widget(txt)
        go = Button(text="Ok", size_hint=(0.1, 1))
        if type == "data":
            go.bind(on_press=lambda x: self.download_data(txt.text))
        elif type == "all_z":
            go.bind(on_press=lambda x: self.download_all_z_data(txt.text))
        elif type == "png":
            go.bind(on_press=lambda x: self.download_png_plot(txt.text))
        elif type == "pdf":
            go.bind(on_press=lambda x: self.download_pdf_plot(txt.text))
        go.bind(on_release=lambda x: self.close_popups(popup))
        close = Button(text="Close", size_hint=(0.2, 1), font_size=self.home.font)
        close.bind(on_press=popup.dismiss)
        content.add_widget(go)
        content.add_widget(close)
        popup.open()

    def close_popups(self, fpop):
        """
        Close file name popup and plot popup

        Args:
            fpop: reference to file name popup
        """
        fpop.dismiss()
        self.dismiss()

    def download_png_plot(self, f_name):
        """
        Download the current plot as a PNG file if valid file name given

        Args:
            f_name: String, proposed file name
        """
        file = func.check_file(self.home.rel_path, f_name, ".png")
        if file is False:
            func.alert("Invalid File Name", self.home)
            return
        else:
            path = self.home.rel_path / (file + ".png")
            self.plot.texture.save(str(path.absolute()))
            img = cv2.flip(cv2.imread(str(path.absolute())), 0)
            cv2.imwrite(str(path.absolute()), img)
            func.alert("Download Complete", self.home)

    def download_pdf_plot(self, f_name):
        """
        Download the current plot as a PDF file if valid file name given

        Args:
            f_name: String, proposed file name
        """
        file = func.check_file(self.home.rel_path, f_name, ".pdf")
        if file is False:
            func.alert("Invalid File Name", self.home)
            return
        else:
            ipath = self.home.rel_path / (file + ".png")
            ppath = self.home.rel_path / (file + ".pdf")
            self.plot.texture.save(str(ipath.absolute()))
            img = cv2.flip(cv2.imread(str(ipath.absolute())), 0)
            cv2.imwrite(str(ipath.absolute()), img)
            with open(str(ppath.absolute()), "wb") as f:
                f.write(img2pdf.convert(str(ipath.absolute())))
            func.alert("Download Complete", self.home)

    def download_data(self, f_name):
        """
        Downloads transect data for selections into a JSON file if valid file name given.

        Args:
            f_name: String, proposed file name
        """
        file = func.check_file(self.home.rel_path, f_name, ".json")
        if file is False:
            func.alert("Invalid File Name", self.home)
            return
        else:  # Build correctly formatted JSON file
            dat = copy.copy(self.active_data)
            if len(self.active_vars) == 0:  # If Image
                final = self.add_marker_info(dat)
            elif len(self.active_z) == 0:  # If 2D NetCDF
                final = {}
                for var in list(dat.keys()):
                    final[var] = self.add_marker_info(dat[var])
            else:  # If 3D NetCDF
                final = {}
                for var in list(dat.keys()):
                    final[var] = {}
                    for z in list(dat[var].keys()):
                        final[var][z] = self.add_marker_info(dat[var][z])
            with open(self.home.rel_path / (file + ".json"), "w") as f:
                json.dump(final, f)

            func.alert("Download Complete", self.home)

    def add_marker_info(self, dicti):
        """
        Adds back fields removed for plotting purposes if marker tool was used

        Args:
            dicti: Dictionary of transect data from either transect marker or regular transect tool

        Returns:
            dicti: Dictionary of transect data with 'Click X', 'Click Y', and 'Width' fields added back
                in if transect marker tool was used.
        """
        if list(dicti.keys())[0] != "Multi":
            for marker in list(dicti.keys()):
                dicti[marker]['Click X'] = self.all_transects[marker]['Click X']
                dicti[marker]['Click Y'] = self.all_transects[marker]['Click Y']
                dicti[marker]['Width'] = self.all_transects[marker]['Width']
        return dicti

    def download_all_z_data(self, f_name):
        """
        Get and download data for all selected variables for all z dimension values.

        Args:
            f_name: String, proposed file name
        """
        file = func.check_file(self.home.rel_path, f_name, ".json")
        if file is False:
            func.alert("Invalid File Name", self.home)
            return
        else:
            dat = {}
            ds = self.home.netcdf['file']
            z_len = len(ds.coords[self.home.netcdf['z']].data)
            for var in self.active_vars:
                config = copy.copy(self.home.netcdf)
                config['var'] = var
                ds = ds[config['var']]
                dat[var] = {}
                ds.load()
                ds = ds.rename({config['y']: "y", config['x']: "x", config['z']: "z"})
                ds = ds.transpose('x', 'y', 'z')
                ds['z'] = ds['z'].astype(str)
                ds = ds.data
                for d in range(0, z_len):
                    dat[var][d] = {}
                    curr = ds[:, :, d]
                    for key in list(self.active_transects.keys()):
                        # All markers selected (if marker tool used)
                        dat[var][d][key] = {}
                        for cut in list(self.active_transects[key].keys()):
                            # All selected transects
                            if self.active_transects[key][cut]:
                                if cut == "Average":
                                    dat[var][d][key][cut] = self.get_average(key, curr)
                                else:
                                    dat[var][d][key][cut] = func.ip_get_points(self.all_transects[key][cut], curr,
                                                                               self.home.nc)
                        if len(dat[var][d][key]) == 0:
                            dat[var][d].pop(key)

            with open(self.home.rel_path / (file + ".json"), "w") as f:
                json.dump(dat, f)
            func.alert("Download Complete", self.home)

    def get_marker_dropdown(self):
        """
        Build dropdown menu for marker options with sub-menus for the individual transects

        Returns:
            BackgroundDropDown for marker options
        """
        # Get dropdown for marker options
        marker_list = BackgroundDropDown(auto_width=False, width=dp(180), max_height=dp(300))
        for i in list(self.all_transects.keys()):
            m_box = ui.boxlayout.BoxLayout(spacing=dp(10), padding=dp(10), size_hint_y=None, height=dp(40),
                                           width=dp(180))
            btn = func.RoundedButton(text=i, size_hint=(0.5, 1))
            btn.bind(on_press=lambda but=btn, txt=i: self.cut_drop(txt, but))
            m_box.add_widget(btn)
            marker_list.add_widget(m_box)
        return marker_list

    def cut_drop(self, marker, button):
        """
        Attaches transect dropdowns to marker buttons in marker dropdown menu

        Args:
            marker: String, marker label 'Marker #'
            button: RoundedButton, marker's button in marker dropdown menu
        """
        temp_cut_drop = self.get_cut_dropdown(marker)
        temp_cut_drop.open(button)

    def get_cut_dropdown(self, key):
        """
        Build dropdown menu for selecting transects.

        Args:
            key: String, name of marker selecting from 'Marker #' or 'Multi' if marker tool wasn't used

        Returns:
            BackgroundDropDown for transect options
        """
        # Get dropdown for transect options
        drop = BackgroundDropDown(auto_width=False, width=dp(180), max_height=dp(200))
        for i in list(self.active_transects[key].keys()):
            c_box = ui.boxlayout.BoxLayout(spacing=dp(5), size_hint_y=None, height=dp(40), width=dp(180))
            lab = Label(text=i, size_hint=(0.5, 1))
            c_box.add_widget(lab)
            check = CheckBox(active=self.active_transects[key][i], size_hint=(0.5, 1))
            check.bind(active=lambda x, y, m=key, t=i: self.on_transect_checkbox(x, m, t))
            c_box.add_widget(check)
            drop.add_widget(c_box)
        return drop

    def on_transect_checkbox(self, check, marker, cut, *args):
        """
        Updates plot when a transect checkbox is clicked. Safeguards so at least one transect
        is always selected.

        Args:
            check: Reference to checkbox in transect list
            marker: String, name of marker selecting from 'Marker #' or 'Multi' if marker tool wasn't used
            cut: String, name of transect 'Cut #'
        """
        # Select or deselect transect
        self.active_transects[marker][cut] = not self.active_transects[marker][cut]

        # Check this isn't the last transect selected
        count = 0
        for key in list(self.active_transects.keys()):  # Count current transects
            count += sum(self.active_transects[key].values())
        if count == 0:  # If last transect unchecked, recheck and ignore
            self.active_transects[marker][cut] = not self.active_transects[marker][cut]
            check.active = True
            return
        else:
            # Update current data
            self.active_data = self.get_data()
            # Update plot
            self.plotting.remove_widget(self.plot)
            self.plot_active()
            temp = io.BytesIO()
            plt.savefig(temp, format="png")
            temp.seek(0)
            plt.close()
            self.plot = ui.image.Image(source="", texture=CoreImage(io.BytesIO(temp.read()), ext="png").texture,
                                       size_hint=(0.7, 1))
            self.plotting.add_widget(self.plot, len(self.plotting.children))

    def get_var_dropdown(self):
        """
        Get dropdown for NetCDF variable options. Variable only available if dimensions match current variable

        Returns:
            BackgroundDropdown menu of variable options
        """
        file = self.home.netcdf['file']
        var_list = BackgroundDropDown(auto_width=False, width=dp(180), max_height=dp(300))
        for var in list(file.keys()):
            if file[self.home.netcdf['var']].dims == file[var].dims:  # Dimensions must match variable in viewer
                v_box = ui.boxlayout.BoxLayout(spacing=dp(10), padding=dp(10), size_hint_y=None, height=dp(40),
                                               width=dp(180))
                lab = Label(text=var, size_hint=(0.5, 1))
                v_box.add_widget(lab)
                check = CheckBox(active=var in self.active_vars, size_hint=(0.5, 1))
                check.bind(active=lambda x, y, var=var: self.on_var_checkbox(x, var))
                v_box.add_widget(check)
                var_list.add_widget(v_box)
        return var_list

    def on_var_checkbox(self, check, var, *args):
        """
        Updates plot when a variable checkbox is clicked. Safeguards so at least one variable
        is always selected.

        Args:
            check: Reference to checkbox in variable list
            var: String, name of variable
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

        # Update plot
        self.plotting.remove_widget(self.plot)
        self.plot_active()
        temp = io.BytesIO()
        plt.savefig(temp, format="png")
        temp.seek(0)
        plt.close()
        self.plot = ui.image.Image(source="", texture=CoreImage(io.BytesIO(temp.read()), ext="png").texture,
                                   size_hint=(0.7, 1))
        self.plotting.add_widget(self.plot, len(self.plotting.children))

    def get_z_dropdown(self):
        """
        Get dropdown for NetCDF z value selections

        Returns:
            BackgroundDropDown menu of z value options
        """
        z_list = BackgroundDropDown(auto_width=False, width=dp(180), max_height=dp(300))
        for z in list(self.home.netcdf['file'].coords[self.home.netcdf['z']].data):
            z_box = ui.boxlayout.BoxLayout(spacing=dp(10), padding=dp(10), size_hint_y=None, height=dp(40),
                                           width=dp(180))
            lab = Label(text=str(z), size_hint=(0.5, 1))
            z_box.add_widget(lab)
            check = CheckBox(active=str(z) in self.active_z, size_hint=(0.5, 1))
            check.bind(active=lambda x, y, z=str(z): self.on_z_checkbox(x, z))
            z_box.add_widget(check)
            z_list.add_widget(z_box)
        return z_list

    def on_z_checkbox(self, check, z, *args):
        """
        Updates plot when a z value checkbox is clicked. Safeguards so at least one z value
        is always selected.

        Args:
            check: Reference to checkbox in variable list
            z: String, name of z value
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

        # Update plot
        self.plotting.remove_widget(self.plot)
        self.plot_active()
        temp = io.BytesIO()
        plt.savefig(temp, format="png")
        temp.seek(0)
        plt.close()
        self.plot = ui.image.Image(source="", texture=CoreImage(io.BytesIO(temp.read()), ext="png").texture,
                                   size_hint=(0.7, 1))
        self.plotting.add_widget(self.plot, len(self.plotting.children))

    def get_all_z_plot(self):
        """
        Determines if settings are okay to do an all z value plot. If so calls for plot, if not creates an error
        popup.
        """
        count = 0
        for key in list(self.active_transects.keys()):
            # Count current transects selected
            count += sum(self.active_transects[key].values())
        if count == 1:
            # Go ahead and plot
            self.plot_all_z()
            self.plotting.remove_widget(self.plot)
            temp = io.BytesIO()
            plt.savefig(temp, format="png")
            temp.seek(0)
            plt.close()
            self.plot = ui.image.Image(source="", texture=CoreImage(io.BytesIO(temp.read()), ext="png").texture,
                                       size_hint=(0.7, 1))
            self.plotting.add_widget(self.plot, len(self.plotting.children))
        else:
            # Error popup if more than one transect is selected
            content = ui.boxlayout.BoxLayout()
            error = Popup(title="Error", content=content, size_hint=(0.5, 0.15))
            lab = Label(text="Please only select one transect", size_hint=(0.8, 1))
            close = Button(text="Close", size_hint=(0.2, 1))
            close.bind(on_press=error.dismiss)
            content.add_widget(lab)
            content.add_widget(close)
            error.open()

    def plot_all_z(self):
        """
         Gather all z value plots for all selected variables into one figure

         Returns:
            Final completed figure
        """
        # Determine subplot layout
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

        count = 0
        for var in self.active_vars:
            # Plot variable and assign to subplot
            count += 1
            if count % 2 == 0:
                c = 1
                r = int((count / 2) - 1)
            else:
                c = 0
                r = int(((count + 1) / 2) - 1)
            if row == 1 and col == 1:
                pos = self.z_ip(var, ax)
                fig.colorbar(pos, ax=ax)
            elif row == 1:
                pos = self.z_ip(var, ax[c])
                fig.colorbar(pos, ax=ax[c])
            else:
                pos = self.z_ip(var, ax[r, c])
                fig.colorbar(pos, ax=ax[r, c])
        if len(self.active_vars) % 2 == 1 and len(self.active_vars) > 1:
            plt.delaxes(ax[r, 1])
        return fig

    def z_ip(self, var, ax):
        """
        Gather data and plot all z values for given variable

        Args:
            var: String, Variable name
            ax: Plot axis on which to make plot

        Returns:
            Axis with completed plot
        """
        # Get transect coordinates
        v = self.active_data[var]
        z = v[next(iter(v))]
        marker = next(iter(z))
        tran = next(iter(z[marker]))
        points = self.all_transects[marker][tran]
        width = len(z[marker][tran]['x'])

        ds = self.home.netcdf['file']
        z_len = len(ds.coords[self.home.netcdf['z']].data)
        config = copy.copy(self.home.netcdf)
        config['var'] = var
        ds = ds[config['var']]

        # Load entire dataset (if big file this will take a while but decreases total plot time)
        ds.load()
        ds = ds.rename({config['y']: "y", config['x']: "x", config['z']: "z"})
        ds = ds.transpose('x', 'y', 'z')
        ds['z'] = ds['z'].astype(str)
        ds = ds.data

        # Array of data values at x, y pairs for each z
        all_z = np.empty(shape=(z_len, width))
        c = 0

        for d in range(0, z_len):
            # Get transect data for each z level and add to array
            curr = ds[:, :, d]
            dat = func.ip_get_points(points, curr, self.home.nc)
            all_z[c, :] = dat['Cut']
            c += 1

        # Plot array
        pos = ax.imshow(all_z)
        ax.set_ylabel(self.home.netcdf['z'])
        ax.set_xlabel("Along Transect Point")
        ax.set_title(var)
        return pos

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

        if self.f_type == "Img":  # If image just plot
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
        Creates a single plot of selected transect data for a single variable (if NetCDF)

        Args:
            data: Currently selected transect data. Either self.active_data itself or a sub-dictionary
            ax: Plot axis on which to make plot
            label: Label for the y axis of plot. If NetCDF use variable if Image use 'Mean RGB Value'

        Returns:
            List of string labels for the plot's legend
        """
        # Create a non-nested dictionary of selections with appropriate labels
        dat = copy.copy(data)
        plot_dat = {}
        if list(dat.keys())[0][0:6] != "Marker" and list(dat.keys())[0] != "Multi":
            # Gather data for all transects selected across all markers for all Z levels selected
            for z in list(dat.keys()):
                for obj in list(dat[z].keys()):
                    if obj == "Multi":
                        title = "Z: " + z + " "
                    else:
                        title = "Z: " + z + " M" + obj[-1] + " "
                    for cut in list(dat[z][obj].keys()):
                        if cut == "Average":
                            plot_dat[title + cut] = dat[z][obj][cut]
                        else:
                            plot_dat[title + cut] = dat[z][obj][cut]["Cut"]
        else:
            for obj in list(dat.keys()):
                # Gather data for all transects selected across all markers
                if obj == "Multi":
                    title = ""
                else:
                    title = "M" + obj[-1] + " "
                for cut in list(dat[obj].keys()):
                    if cut == "Average":
                        plot_dat[title + cut] = dat[obj][cut]
                    else:
                        plot_dat[title + cut] = dat[obj][cut]["Cut"]

        # Plot data by turning dictionary into a data frame
        df = pd.DataFrame.from_dict(dict([(k, pd.Series(v)) for k, v in plot_dat.items()]))
        x = np.asarray(df.index)
        axis = (x - x[0]) / (x[-1] - x[0])
        ax.plot(axis, df)

        ax.set_ylabel(label.capitalize())
        if not self.home.nc:
            ax.set_ylim(ymin=0)
        ax.set_xlabel("Normalized Long Transect Distance")
        plt.tight_layout()
        # Return dataframe column names for legend
        return df.columns

    def get_data(self):
        """
        Gathers transect data for currently selected variables, z values, and transects.

        Returns:
            Nested dictionary of transect data with hierarchy:
                Variables -> Z values -> Markers/Multi -> Transects -> X,Y, Cut
            If only 2D NetCDF file there is no Z values level. If an image there is no Variables or Z Values level.
        """
        # Get transect data for list of active transect points
        config = copy.copy(self.home.netcdf)
        values = {}
        if len(self.active_vars) >= 1:
            # If data has variables
            for var in self.active_vars:
                values[var] = {}
                config["var"] = var
                if len(self.active_z) >= 1:
                    # If data has multiple Z levels
                    for z in self.active_z:
                        # Multi Z selection
                        values[var][z] = {}
                        config["z_val"] = z
                        curr = self.home.sel_data(config)
                        for key in list(self.active_transects.keys()):
                            # All markers selected
                            values[var][z][key] = {}
                            for cut in list(self.active_transects[key].keys()):
                                # All selected transects
                                if self.active_transects[key][cut]:
                                    if cut == "Average":
                                        values[var][z][key][cut] = self.get_average(key, curr)
                                    else:
                                        values[var][z][key][cut] = func.ip_get_points(self.all_transects[key][cut],
                                                                                      curr, self.home.nc)
                            if len(values[var][z][key]) == 0:
                                values[var][z].pop(key)
                else:
                    curr = self.home.sel_data(config)
                    # Single Z Selection
                    for key in list(self.active_transects.keys()):
                        # All markers selected
                        values[var][key] = {}
                        for cut in list(self.active_transects[key].keys()):
                            if self.active_transects[key][cut]:
                                # All transects selected
                                if cut == "Average":
                                    values[var][key][cut] = self.get_average(key, curr)
                                else:
                                    values[var][key][cut] = func.ip_get_points(self.all_transects[key][cut],
                                                                               curr, self.home.nc)
                        if len(values[var][key]) == 0:
                            values[var].pop(key)
        else:
            curr = self.home.rgb
            # Image data (no variables, no Z levels)
            for key in list(self.active_transects.keys()):
                # All markers selected
                values[key] = {}
                for cut in list(self.active_transects[key].keys()):
                    # All transects selected
                    if self.active_transects[key][cut]:
                        if cut == "Average":
                            values[key][cut] = self.get_average(key, curr)
                        else:
                            values[key][cut] = func.ip_get_points(self.all_transects[key][cut], curr, self.home.nc)
                if len(values[key]) == 0:
                    values.pop(key)
        return values

    def get_average(self, key, curr):
        """
        Finds average of all transects in a marker. Transect width must be the same for the entire marker.
        
        Args:
            key: String, 'Marker #'
            curr: 2D array, currently loaded dataset

        Returns:
            1D array of length of transect width containing average transect values for the marker.
        """
        # Gets average of all transects in a marker
        # Assumes all transects are same length
        dat = np.zeros(self.all_transects[key]['Width'][0])
        for cut in list(self.all_transects[key].keys())[3:]:
            dat += func.ip_get_points(self.all_transects[key][cut], curr, self.home.nc)['Cut']
        dat = dat / len(list(self.all_transects[key].keys())[3:])
        return list(dat)
