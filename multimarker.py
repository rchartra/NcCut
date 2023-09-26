"""
Class for multiple marker tool that allows user to have multiple markers on screen at once.
"""

import kivy.uix as ui
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.core.window import Window
from os.path import exists
import json
import functions as func
from marker import Marker
from markerwidth import MarkerWidth
from plotpopup import PlotPopup


class Click:
    # Mimic a user click
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.pos = (x, y)


class MultiMarker(ui.widget.Widget):
    # Creates, stores, and manages downloads for multiple markers
    def __init__(self, home, **kwargs):
        super(MultiMarker, self).__init__(**kwargs)
        self.m_on = False
        self.home = home
        self.dbtn = func.RoundedButton(text="Plot", size_hint=(1, 0.1), font_size=self.size[0] / 10)
        self.dbtn.bind(on_press=lambda x: self.gather_popup())
        self.dragging = False
        self.font = 8
        self.width_w = MarkerWidth(self, size_hint=(1, 0.1))
        self.clicks = 0
        self.twidth = 40
        self.cir_size = self.home.cir_size

        # Upload Button
        self.upbtn = func.RoundedButton(text="Upload Project", size_hint=(1, 0.1), font_size=self.size[0] / self.font)
        self.upbtn.bind(on_press=lambda x: self.upload_pop())
        self.home.ids.sidebar.add_widget(self.upbtn, 1)

        # New Line Button
        self.nbtn = func.RoundedButton(text="New Line", size_hint=(1, 0.1), font_size=self.size[0] / self.font)

        self.nbtn.bind(on_press=lambda x: self.new_line())
        self.home.ids.sidebar.add_widget(self.nbtn, 1)

    def upload_pop(self):
        # Popup asking for project file
        content = ui.boxlayout.BoxLayout(orientation='horizontal')
        popup = Popup(title="File Name", content=content, size_hint=(0.5, 0.15))
        txt = TextInput(size_hint=(0.7, 1), hint_text="Enter File Name")
        content.add_widget(txt)
        go = Button(text="Ok", size_hint=(0.1, 1))
        go.bind(on_release= lambda x: self.check_file(txt.text, popup))
        close = Button(text="Close", size_hint=(0.2, 1))
        close.bind(on_press=popup.dismiss)
        content.add_widget(go)
        content.add_widget(close)
        popup.open()

    def check_file(self, file, popup):
        # Check if given file is a json file containing marker data
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
        # Adds markers by "clicking" the points in the file with the marker width denoted by the file
        for m in dat.keys():

            marker = Marker(home=self.home)
            clicks = tuple(zip(dat[m]["Click X"], dat[m]["Click Y"], dat[m]["Width"]))
            self.add_widget(marker)

            for i in clicks:
                marker.twidth = i[2]
                marker.on_touch_down(Click(i[0], i[1]))
            marker.stop_drawing()
        self.marker_off()

    def update_width(self, num):
        # Update marker width
        self.twidth = num
        self.children[0].twidth = num

    def del_line(self):
        # If only one, delete but add new marker, otherwise delete current and go to previous
        if len(self.children) == 0:
            return
        Window.unbind(mouse_pos=self.children[0].draw_line)
        self.remove_widget(self.children[0])
        if len(self.children) == 0:
            self.clicks = 0
            self.home.img.current.remove(self.dbtn)
            self.home.img.current.remove(self.width_w)
            self.new_line()

    def del_point(self):
        if len(self.children) == 0:
            return
        elif self.children[0].clicks == 0:
            if len(self.children) > 1:
                self.remove_widget(self.children[0])
            else:
                return
        self.children[0].del_point()

    def new_line(self):
        # Creates a new marker
        if not self.dragging or self.home.img.editing:
            if len(self.children) == 0 or self.children[0].clicks >= 2:
                if len(self.children) != 0:
                    self.children[0].stop_drawing()
                m = Marker(home=self.home)
                self.add_widget(m)

    def marker_off(self):
        # Update whether there is currently a marker on the board
        self.m_on = False

    def gather_popup(self):
        frames = {}
        c = 1
        for i in reversed(self.children):
            data = {}
            data['Click X'], data['Click Y'], data['Width'] = map(list, zip(*i.points))
            count = 1
            for j in i.base.lines:
                data["Cut " + str(count)] = j.line.points
                count += 1
            frames["Marker " + str(c)] = data
            c += 1

        PlotPopup(frames, self.home)

    def on_touch_down(self, touch):
        # Manage download and marker width widgets when all markers are deleted
        if not self.dragging:
            self.clicks += 1
            if self.clicks == 1:
                self.home.ids.sidebar.add_widget(self.width_w, 1)
            if self.clicks == 2:
                self.home.ids.sidebar.add_widget(self.dbtn, 1)
            # If no current marker, create marker. Otherwise, pass touch to current marker.
            if not self.m_on:
                self.new_line()
                self.update_width(self.twidth)
                self.m_on = True
            self.children[0].on_touch_down(touch)
