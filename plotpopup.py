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
import time


class BackgroundDropDown(DropDown):
    def open(self, widget):
        super(BackgroundDropDown, self).open(widget)
        with self.canvas.before:
            Color(rgb=[0.2, 0.2, 0.2])
            self.rect = Rectangle(size=self.size, pos=self.pos, radius=[10, ])
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class PlotPopup(Popup):
    # Popup with plotting and downloading selections
    def __init__(self, transects, home, **kwargs):
        super(PlotPopup, self).__init__(**kwargs)
        self.home = home
        self.all_transects = transects
        if list(self.all_transects.keys())[0][0:-2] == "Marker":
            self.t_type = "Marker"
        else:
            self.t_type = "Multi"

        # Create dictionary of which transects are selected

        self.active_transects = {}
        act = copy.deepcopy(self.all_transects)
        for key in list(act.keys()):
            self.active_transects[key] = {}
            if self.t_type == "Marker":
                act[key].pop("Click X")
                act[key].pop("Click Y")
                act[key].pop("Width")
            self.active_transects[key] = dict.fromkeys(act[key], False)

            # If marker and all values same width, add an average opt   ion
            if self.t_type == "Marker":
                w_lis = self.all_transects[key]['Width']
                if all(x == w_lis[0] for x in w_lis):
                    new = {"Average": False}
                    new.update(self.active_transects[key])
                    self.active_transects[key] = new
        first = list(self.active_transects.keys())[0]
        self.active_transects[first] = dict.fromkeys(self.active_transects[first], True)
        if self.t_type == "Marker":
            w_lis = self.all_transects[first]['Width']
            if all(x == w_lis[0] for x in w_lis):
                self.active_transects[first]["Average"] = False

        # Initialize selections
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

        self.z_plot = False
        self.active_data = self.get_data()
        self.plot_active()
        temp = io.BytesIO()
        plt.savefig(temp, format="png")
        temp.seek(0)
        plt.close()

        # Popup Graphics Code

        self.plot = ui.image.Image(source="", texture=CoreImage(io.BytesIO(temp.read()), ext="png").texture,
                                   size_hint=(0.7, 1))
        self.plotting = ui.boxlayout.BoxLayout(spacing=dp(20), size_hint=(1, 0.9))
        self.plotting.add_widget(self.plot)
        self.title = "Plot Transects"
        self.content = ui.boxlayout.BoxLayout(orientation='vertical', spacing=dp(20), padding=dp(20))
        self.size_hint = (0.8, 0.8)
        sidebar = ui.boxlayout.BoxLayout(orientation='vertical', size_hint=(0.3, 1), padding=dp(10), spacing=dp(20))

        # Transect selection
        t_box = ui.boxlayout.BoxLayout(size_hint=(1, 0.2), spacing=dp(30))
        lab = Label(text="Select Transects: ", size_hint=(0.3, 1), font_size=self.size[0] / 9)
        t_box.add_widget(lab)
        self.t_select = func.RoundedButton(text="Select...", size_hint=(0.7, 1),
                                           font_size=self.size[0] / 9)
        t_box.add_widget(self.t_select)
        if self.t_type == "Marker":
            t_drop = self.get_marker_dropdown()
        else:
            t_drop = self.get_cut_dropdown('Multi')
        self.t_select.bind(on_press=lambda x: t_drop.open(self.t_select))
        sidebar.add_widget(t_box)

        if self.home.nc:
            self.active_var = [self.home.netcdf['var']]
            # Variable Selection
            v_box = ui.boxlayout.BoxLayout(size_hint=(1, 0.2), spacing=dp(30))
            v_box.add_widget(Label(text="Select Variables: ", size_hint=(0.3, 1), font_size=self.size[0] / 9))
            self.v_select = func.RoundedButton(text="Select...", size_hint=(0.7, 1),
                                               font_size=self.size[0] / 9)
            v_box.add_widget(self.v_select)
            v_drop = self.get_var_dropdown()
            self.v_select.bind(on_press=lambda x: v_drop.open(self.v_select))
            sidebar.add_widget(v_box)
            if self.home.netcdf['z'] != "Select...":
                # Z Selection
                z_box = ui.boxlayout.BoxLayout(size_hint=(1, 0.2), spacing=dp(30))
                z_box.add_widget(Label(text="Select Z Values: ", size_hint=(0.3, 1), font_size=self.size[0] / 9))
                self.z_select = func.RoundedButton(text="Select...", size_hint=(0.7, 1),
                                                   font_size=self.size[0] / 9)
                z_box.add_widget(self.z_select)
                z_drop = self.get_z_dropdown()
                self.z_select.bind(on_press=lambda x: z_drop.open(self.z_select))
                sidebar.add_widget(z_box)

                # Z Interpolated
                zp_box = ui.boxlayout.BoxLayout(size_hint=(1, 0.2), spacing=dp(30))
                zp_btn = func.RoundedButton(text="Plot all Z as Img", font_size=self.size[0] / 9)
                zp_btn.bind(on_press=lambda x: self.get_all_z_plot())
                zp_box.add_widget(zp_btn)
                sidebar.add_widget(zp_box)
            else:
                sidebar.add_widget(Label(text="", size_hint=(1, 0.6)))
        else:
            sidebar.add_widget(Label(text="", size_hint=(1, 0.8)))

        self.plotting.add_widget(sidebar)
        self.content.add_widget(self.plotting)

        # Saving Data/Plot

        buttons = ui.boxlayout.BoxLayout(orientation='horizontal', size_hint=(1, .1), spacing=dp(10))

        data_btn = func.RoundedButton(text="Save Selected Data", size_hint=(.4, 1))
        data_btn.bind(on_press=lambda x: self.file_input('data'))

        png_btn = func.RoundedButton(text='Save Plot to PNG', size_hint=(.4, 1))
        png_btn.bind(on_press=lambda x: self.file_input('png'))

        pdf_btn = func.RoundedButton(text='Save Plot to PDF', size_hint=(.4, 1))
        pdf_btn.bind(on_press=lambda x: self.file_input('pdf'))

        close = func.RoundedButton(text="Close", size_hint=(.2, 1))
        close.bind(on_press=self.dismiss)

        buttons.add_widget(data_btn)
        buttons.add_widget(png_btn)
        buttons.add_widget(pdf_btn)
        buttons.add_widget(close)
        self.content.add_widget(buttons)

        self.open()

    def file_input(self, type):
        # Popup window for input of name for plot/json file
        content = ui.boxlayout.BoxLayout(orientation='horizontal')
        popup = Popup(title="File Name", content=content, size_hint=(0.5, 0.15))
        txt = TextInput(size_hint=(0.7, 1), hint_text="Enter File Name")
        content.add_widget(txt)
        go = Button(text="Ok", size_hint=(0.1, 1))
        if type == "data":
            go.bind(on_press=lambda x: self.download_data(txt.text))
        elif type == "png":
            go.bind(on_press=lambda x: self.download_png_plot(txt.text))
        else:
            go.bind(on_press=lambda x: self.download_pdf_plot(txt.text))
        go.bind(on_release=lambda x: self.close_popups(popup))
        close = Button(text="Close", size_hint=(0.2, 1))
        close.bind(on_press=popup.dismiss)
        content.add_widget(go)
        content.add_widget(close)
        popup.open()

    def close_popups(self, fpop):
        # Close file name popup and plot popup
        fpop.dismiss()
        self.dismiss()

    def download_png_plot(self, f_name):
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
        # Downloads Selected Data into JSON file
        file = func.check_file(self.home.rel_path, f_name, ".json")
        if file is False:
            func.alert("Invalid File Name", self.home)
            return
        else:
            with open(self.home.rel_path / (file + ".json"), "w") as f:
                json.dump(self.active_data, f)

            func.alert("Download Complete", self.home)

    def get_marker_dropdown(self):
        marker_list = BackgroundDropDown(auto_width=False, width=dp(180), max_height=dp(300))
        for i in list(self.all_transects.keys()):
            m_box = ui.boxlayout.BoxLayout(spacing=dp(10), padding=dp(10), size_hint_y=None, height=dp(40), width=dp(180))
            btn = func.RoundedButton(text=i, size_hint=(0.5, 1))
            btn.bind(on_press=lambda but=btn, txt=i: self.cut_drop(txt, but))
            m_box.add_widget(btn)
            #check = CheckBox(size_hint=(0.5, 1))
            #m_box.add_widget(check)
            marker_list.add_widget(m_box)
        return marker_list

    def cut_drop(self, marker, button):
        temp_cut_drop = self.get_cut_dropdown(marker)
        temp_cut_drop.open(button)

    def get_cut_dropdown(self, key):
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
        self.active_transects[marker][cut] = not self.active_transects[marker][cut]
        # Check this isn't the last transect selected
        count = 0
        for key in list(self.active_transects.keys()):
            count += sum(self.active_transects[key].values())
        if count == 0:
            self.active_transects[marker][cut] = not self.active_transects[marker][cut]
            check.active = True
            return
        else:
            self.active_data = self.get_data()
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
        var_list = BackgroundDropDown(auto_width=False, width=dp(180), max_height=dp(300))
        for var in list(self.home.netcdf['file'].keys()):
            v_box = ui.boxlayout.BoxLayout(spacing=dp(10), padding=dp(10), size_hint_y=None, height=dp(40), width=dp(180))
            lab = Label(text=var, size_hint=(0.5, 1))
            v_box.add_widget(lab)
            check = CheckBox(active=var in self.active_vars, size_hint=(0.5, 1))
            check.bind(active=lambda x, y, var=var: self.on_var_checkbox(x, var))
            v_box.add_widget(check)
            var_list.add_widget(v_box)
        return var_list

    def on_var_checkbox(self, check, var, *args):
        if var in self.active_vars:
            self.active_vars.remove(var)
        else:
            self.active_vars.append(var)
        if not self.active_vars:
            self.active_vars.append(var)
            check.active = True
        self.active_data = self.get_data()
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
        if z in self.active_z:
            self.active_z.remove(z)
        else:
            self.active_z.append(z)
        if not self.active_z:
            self.active_z.append(z)
            check.active = True
        self.active_data = self.get_data()
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
        count = 0
        for key in list(self.active_transects.keys()):
            count += sum(self.active_transects[key].values())
        if count == 1:
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
            content = ui.boxlayout.BoxLayout()
            error = Popup(title="Error", content=content, size_hint=(0.5, 0.15))
            lab = Label(text="Please only select one transect", size_hint=(0.8, 1))
            close = Button(text="Close", size_hint=(0.2, 1))
            close.bind(on_press=error.dismiss)
            content.add_widget(lab)
            content.add_widget(close)
            error.open()

    def plot_all_z(self):
        # Check only one transect is selected
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
            count += 1
            if count % 2 == 0:
                c = 1
                r = int((count / 2) - 1)
            else:
                c = 0
                r = int(((count + 1) / 2) - 1)
            if row == 1 and col == 1:
                self.z_ip(var, ax)
            elif row == 1:
                self.z_ip(var, ax[c])
            else:
                self.z_ip(var, ax[r, c])
        if len(self.active_vars) % 2 == 1 and len(self.active_vars) > 1:
            plt.delaxes(ax[r, 1])
        self.z_plot = True
        return fig

    def z_ip(self, var, ax):
        t0 = time.time()
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
        t0 = time.time()
        ds.load()
        t1 = time.time()
        print("loading dataset: " + str(t1 - t0))
        ds = ds.rename({config['y']: "y", config['x']: "x", config['z']: "z"})
        ds = ds.transpose('x', 'y', 'z')
        ds['z'] = ds['z'].astype(str)
        ds = ds.data

        # Array of data values at x, y pairs for each z
        all_z = np.empty(shape=(z_len, width))
        c = 0

        for d in range(0, z_len):
            curr = ds[:, :, d]
            dat = func.ip_get_points(points, curr, self.home.nc)
            all_z[c, :] = dat['Cut']
            c += 1

        ax.imshow(all_z)
        ax.set_ylabel(self.home.netcdf['z'])
        ax.set_xlabel("Along Transect Point")
        t1 = time.time()
        print("z_ip(): " + str(t1 - t0))

    def plot_active(self):
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
        if self.f_type == "Img":
            names = self.plot_single(self.active_data, ax, "Mean RGB Value")
        else:
            count = 0
            for var in self.active_vars:
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
                plt.delaxes(ax[r, 1])
        fig.legend(names, title="Legend", bbox_to_anchor=(1, 1))
        self.z_plot = False
        return fig

    def plot_single(self, data, ax, var):
        # Create plots
        dat = copy.copy(data)
        plot_dat = {}
        if list(dat.keys())[0][0:6] != "Marker" and list(dat.keys())[0] != "Multi":
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
                if obj == "Multi":
                    title = ""
                else:
                    title = "M" + obj[-1] + " "
                for cut in list(dat[obj].keys()):
                    if cut == "Average":
                        plot_dat[title + cut] = dat[obj][cut]
                    else:
                        plot_dat[title + cut] = dat[obj][cut]["Cut"]

        df = pd.DataFrame.from_dict(dict([(k, pd.Series(v)) for k, v in plot_dat.items()]))
        x = np.asarray(df.index)
        axis = (x - x[0]) / (x[-1] - x[0])
        ax.plot(axis, df)

        ax.set_ylabel(var.capitalize())
        if not self.home.nc:
            ax.set_ylim(ymin=0)
        ax.set_xlabel("Normalized Long Transect Distance")
        plt.tight_layout()
        return df.columns

    def get_data(self):
        config = copy.copy(self.home.netcdf)
        values = {}
        if len(self.active_vars) >= 1:
            for var in self.active_vars:
                values[var] = {}
                config["var"] = var
                if len(self.active_z) >= 1:
                    for z in self.active_z:
                        values[var][z] = {}
                        config["z_val"] = z
                        curr = self.home.sel_data(config)
                        for key in list(self.active_transects.keys()):
                            values[var][z][key] = {}
                            for cut in list(self.active_transects[key].keys()):
                                if self.active_transects[key][cut]:
                                    if cut == "Average":
                                        values[var][z][key][cut] = self.get_average(key, curr)
                                    else:
                                        values[var][z][key][cut] = func.ip_get_points(self.all_transects[key][cut], curr, self.home.nc)
                            if len(values[var][z][key]) == 0:
                                values[var][z].pop(key)
                else:
                    curr = self.home.sel_data(config)
                    for key in list(self.active_transects.keys()):
                        values[var][key] = {}
                        for cut in list(self.active_transects[key].keys()):
                            if self.active_transects[key][cut]:
                                if cut == "Average":
                                    values[var][key][cut] = self.get_average(key, curr)
                                else:
                                    values[var][key][cut] = func.ip_get_points(self.all_transects[key][cut], curr, self.home.nc)
                        if len(values[var][key]) == 0:
                            values[var].pop(key)
        else:
            curr = self.home.rgb
            for key in list(self.active_transects.keys()):
                values[key] = {}
                for cut in list(self.active_transects[key].keys()):
                    if self.active_transects[key][cut]:
                        if cut == "Average":
                            values[key][cut] = self.get_average(key, curr)
                        else:
                            values[key][cut] = func.ip_get_points(self.all_transects[key][cut], curr, self.home.nc)
                if len(values[key]) == 0:
                    values.pop(key)
        return values

    def get_average(self, key, curr):
        # Gets average of all transects in a marker
        # Assumes all transects are same length
        dat = np.zeros(self.all_transects[key]['Width'][0])
        for cut in list(self.all_transects[key].keys())[3:]:
            dat += func.ip_get_points(self.all_transects[key][cut], curr, self.home.nc)['Cut']
        dat = dat / len(list(self.all_transects[key].keys())[3:])
        return dat
