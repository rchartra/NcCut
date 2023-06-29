import kivy.uix as ui
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.metrics import dp
from os.path import exists
import json
import functions as func
from marker import Marker
from markerwidth import MarkerWidth


class Click:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class MultiMarker(ui.widget.Widget):
    # Creates, stores, and manages downloads for multiple markers
    def __init__(self, home, **kwargs):
        super(MultiMarker, self).__init__(**kwargs)
        self.m_on = False
        self.home = home
        self.dbtn = Button()
        self.width_w = 0
        self.clicks = 0
        self.twidth = 40

        # Upload Button
        self.upbtn = func.RoundedButton(text="Upload Project", pos_hint={'x': .01, 'y': 0.08}, size=(dp(115), dp(30)),
                            size_hint_x=None, size_hint_y=None)
        self.upbtn.bind(on_press=lambda x: self.upload_pop())
        self.home.ids.view.parent.add_widget(self.upbtn)

        # New Line Button
        self.nbtn = func.RoundedButton(text="New Line", pos_hint={'x': .85, 'y': 0.1}, size=(dp(100), dp(30)),
                                       size_hint_x=None, size_hint_y=None)

        self.nbtn.bind(on_press=lambda x: self.marker_off())
        self.home.ids.view.parent.add_widget(self.nbtn)

        # Delete Button
        self.delete = func.RoundedButton(text="Delete", pos_hint={'x': .85, 'y': 0.18}, size=(dp(100), dp(30)),
                                         size_hint_x=None, size_hint_y=None)
        self.delete.bind(on_press=lambda x: self.del_marker())
        self.home.ids.view.parent.add_widget(self.delete)

    def upload_pop(self):
        # Popup asking for file
        content = ui.boxlayout.BoxLayout(orientation='horizontal')
        popup = Popup(title="File Name", content=content, size_hint=(0.5, 0.15))
        txt = TextInput(size_hint=(0.7, 1), hint_text="Enter File Name")
        content.add_widget(txt)
        go = Button(text="Ok", size_hint=(0.3, 1))

        go.bind(on_release= lambda x: self.check_file(txt.text, popup))
        content.add_widget(go)
        popup.open()

    def check_file(self, file, popup):

        if exists(file):
            if file[-5:] == ".json":
                data = json.load(open(file))
                if list(data.keys())[0] == "Marker 1":
                    popup.dismiss()
                    self.upload_data(data)
                else:
                    content = Label(text="Incorrect File Format")
                    popup2 = Popup(title="Error", content=content, size_hint=(0.5, 0.15))
                    popup2.open()
            else:
                content = Label(text="Incorrect File Format")
                popup2 = Popup(title="Error", content=content, size_hint=(0.5, 0.15))
                popup2.open()
        else:
            content = Label(text="File Not Found")
            popup2 = Popup(title="Error", content=content, size_hint=(0.5, 0.15))
            popup2.open()

    def upload_data(self, dat):

        for m in dat.keys():

            marker = Marker(multi=True, home=self.home)
            clicks = tuple(zip(dat[m]["Click X"], dat[m]["Click Y"], dat[m]["Width"]))
            self.add_widget(marker)

            for i in clicks:
                marker.twidth = i[2]
                marker.on_touch_down(Click(i[0], i[1]))
        self.marker_off()

    def update_width(self, num):
        self.twidth = num
        self.children[0].twidth = num

    def del_marker(self):
        # Removes old marker
        # If current line has no clicks, delete current line and prev line
        if self.children[0].clicks == 0:
            self.remove_widget(self.children[0])

        if len(self.children) != 0:
            self.remove_widget(self.children[0])
        if len(self.children) == 0:
            self.clicks = 0
            self.home.ids.view.parent.remove_widget(self.dbtn)
            self.home.ids.view.parent.remove_widget(self.width_w)

        self.new_line()

    def new_line(self):
        # Creates a new marker

        m = Marker(multi=True, home=self.home)
        self.add_widget(m)

    def marker_off(self):
        # Update whether there is currently a marker on the board
        self.m_on = False

    def download_data(self, fname):
        # Create a folder and download each marker's transect data into csv files

        file = func.check_file(fname, ".json")
        if file is False:
            func.alert("Invalid File Name", self.home)
            return
        else:
            # Create json file
            frames = {}
            c = 1

            for i in reversed(self.children):
                data = {}
                data['Click X'], data['Click Y'], data['Width'] = map(list, zip(*i.points))
                count = 1
                for j in i.base.lines:
                    data["Cut " + str(count)] = j.ipGetPoints()
                    count += 1
                frames["Marker " + str(c)] = data
                c += 1

            with open(file + ".json", "w") as f:
                json.dump(frames, f)
            func.alert("Download Complete", self.home)

    def file_input(self):
        # Create popup to ask for name of folder

        content = ui.boxlayout.BoxLayout(orientation='horizontal')
        popup = Popup(title="File Name", content=content, size_hint=(0.5, 0.15))

        txt = TextInput(size_hint=(0.7, 1), hint_text="Enter File Name")
        content.add_widget(txt)

        go = Button(text="Ok", size_hint=(0.3, 1))
        go.bind(on_release=lambda x: self.download_data(txt.text))
        go.bind(on_press=popup.dismiss)

        content.add_widget(go)
        popup.open()

    def on_touch_down(self, touch):

        # Manage download and marker width widgets when all markers are deleted
        self.clicks += 1
        if self.clicks == 1:
            self.width_w = MarkerWidth(self, size_hint=(0.15, 0.06), orientation='horizontal', pos_hint={'x': 0.01, 'y': 0.01})
            self.home.ids.view.parent.add_widget(self.width_w)
        if self.clicks == 2:
            self.dbtn = func.RoundedButton(text="Download", pos_hint={'x': .85, 'y': 0.02}, size=(dp(100), dp(30)),
                                           size_hint_x=None, size_hint_y=None)
            self.dbtn.bind(on_press=lambda x: self.file_input())
            self.home.ids.view.parent.add_widget(self.dbtn)
        # If no current marker, create marker. Otherwise pass touch to current marker.
        if not self.m_on:
            self.new_line()
            self.update_width(self.twidth)
            self.m_on = True
        self.children[0].on_touch_down(touch)
