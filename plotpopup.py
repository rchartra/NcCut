
import kivy.uix as ui
from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.uix.dropdown import DropDown
import functions as func
import os
import copy
import json


class PlotPopup(Popup):
    def __init__(self, data, home, **kwargs):
        super(PlotPopup, self).__init__(**kwargs)
        self.home = home
        self.all_data = data
        self.active_data = copy.copy(self.all_data)
        self.curr_marker = 0
        self.type = list(data.keys())[0][0:-2]

        content = ui.boxlayout.BoxLayout(orientation='vertical', spacing=dp(20), padding=dp(20))
        self.plotting = ui.boxlayout.BoxLayout(spacing=dp(20), size_hint=(1, 0.9))

        if self.type == "Marker":
            func.plotdf(self.active_data[list(self.active_data.keys())[0]], self.home)
        elif self.type == "Cut":
            func.plotdf(self.active_data, self.home)

        self.title = "Plot Transects"
        self.content = content
        self.size_hint = (0.8, 0.8)

        self.plot = ui.image.Image(source='____.jpg', size_hint=(0.7, 1))
        self.plot.reload()
        self.plotting.add_widget(self.plot)
        os.remove("____.jpg")

        sidebar = ui.boxlayout.BoxLayout(orientation='vertical', size_hint=(0.3, 1))
        if self.type == "Marker":
            sidebar.add_widget(self.get_marker_dropdown())
            self.curr_marker = list(self.all_data.keys())[0]

        self.checklist = self.get_checklist()
        sidebar.add_widget(self.checklist)
        self.plotting.add_widget(sidebar)
        content.add_widget(self.plotting)

        buttons = ui.boxlayout.BoxLayout(orientation='horizontal', size_hint=(1, .1), spacing=5)

        data_btn = func.RoundedButton(text="Save Selected Data", size_hint=(.4, 1))
        data_btn.bind(on_press=lambda x: self.file_input('data'))

        jpg_btn = func.RoundedButton(text='Save Plot', size_hint=(.4, 1))
        jpg_btn.bind(on_press=lambda x: self.file_input('plot'))

        close = func.RoundedButton(text="Close", size_hint=(.2, 1))
        close.bind(on_press=self.dismiss)

        buttons.add_widget(data_btn)
        buttons.add_widget(jpg_btn)
        buttons.add_widget(close)
        content.add_widget(buttons)

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
        else:
            go.bind(on_press=lambda x: self.download_plot(txt.text))
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

    def download_plot(self, fname):
        # Code to make and download plot of a single transect
        func.plotdf(self.active_data[self.curr_marker], self.home)
        file = func.check_file(self.home.rel_path, fname, ".jpg")
        if file is False:
            func.alert("Invalid File Name", self.home)
            os.remove("____.jpg")
            return
        else:
            path = self.home.rel_path / (file + ".jpg")
            os.rename("____.jpg", str(path))
            func.alert("Download Complete", self.home)

    def download_data(self, fname):
        # Downloads data into a json file
        file = func.check_file(self.home.rel_path, fname, ".json")
        if file is False:
            func.alert("Invalid File Name", self.home)
            return
        else:
            # To json code
            with open(self.home.rel_path / (file + ".json"), "w") as f:
                json.dump(self.active_data, f)

            func.alert("Download Complete", self.home)

    def on_checkbox(self, *args):
        active = [box.children[1].text for box in self.checklist.children if box.children[0].active]
        if not active:
            return
        if self.type == "Marker":
            current = [self.all_data[self.curr_marker][key] for key in active]
            self.active_data[self.curr_marker] = {'Click X': self.all_data[self.curr_marker]['Click X'],
                                                  'Click Y': self.all_data[self.curr_marker]['Click Y'],
                                                  'Width': self.all_data[self.curr_marker]['Width']}
            self.active_data[self.curr_marker].update(dict(zip(reversed(active), reversed(current))))
            func.plotdf(self.active_data[self.curr_marker], self.home)
        elif self.type == "Cut":
            current = [self.all_data[key] for key in active]
            self.active_data = dict(zip(reversed(active), reversed(current)))
            func.plotdf(self.active_data, self.home)
        self.plotting.remove_widget(self.plot)
        self.plot = ui.image.Image(source='____.jpg', size_hint=(0.7, 1))
        self.plot.reload()
        self.plotting.add_widget(self.plot, len(self.plotting.children))
        os.remove("____.jpg")

    def get_checklist(self):
        if self.type == "Marker":
            dat = self.all_data[self.curr_marker]
            active = self.active_data[self.curr_marker]
        elif self.type == "Cut":
            dat = self.all_data
            active = self.active_data

        check_list = ui.boxlayout.BoxLayout(orientation='vertical', size_hint=(1, 0.8), spacing=dp(10))
        items = [item for item in list(dat.keys()) if item != "Width" and item != "Click X" and item != "Click Y"]
        for cut in items:
            box = ui.boxlayout.BoxLayout()
            title = ui.label.Label(text=cut, size_hint=(0.5, 1))
            box.add_widget(title)
            check = CheckBox(active=cut in list(active.keys()), size_hint=(0.5, 1))
            check.bind(active=self.on_checkbox)
            box.add_widget(check)
            check_list.add_widget(box)
        return check_list

    def get_marker_dropdown(self):
        box = ui.boxlayout.BoxLayout(size_hint=(1, 0.2), spacing=dp(10))
        box.add_widget(Label(text="Select Marker: ", size_hint=(0.5, 1), font_size=self.size[0] / 9))
        select = func.RoundedButton(text=list(self.all_data.keys())[0], size_hint=(0.5, 1),
                                    font_size=self.size[0] / 9)
        self.marker_list = DropDown()
        for i in list(self.all_data.keys()):
            btn = Button(text=i, size_hint_y=None, height=30)
            btn.bind(on_press=lambda btn: self.marker_select(btn.text, select))
            btn.bind(on_release=self.marker_list.dismiss)
            self.marker_list.add_widget(btn)
        select.bind(on_release=self.marker_list.open)
        box.add_widget(select)
        return box

    def marker_select(self, marker, button):
        button.text = marker
        self.curr_marker = marker
        self.plotting.children[0].remove_widget(self.checklist)
        self.checklist = self.get_checklist()
        self.plotting.children[0].add_widget(self.checklist)
        self.on_checkbox()
