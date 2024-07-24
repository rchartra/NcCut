"""
Transect marker tool widget.

Manages having multiple markers on screen at once and the uploading of previous projects.
"""

import kivy.uix as ui
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.core.window import Window
from os.path import exists
import json
import nccut.functions as func
from nccut.marker import Marker
from nccut.markerwidth import MarkerWidth
from nccut.plotpopup import PlotPopup


class Click:
    """
    Object that mimics a user click.

    Attributes:
        x (float): X coordinate of click point
        y (float): Y coordinate of click point
        pos (tuple): 2 element tuple: (X coord, Y coord)
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.pos = (x, y)


def correct_test(data):
    """
    Check if dictionary has necessary fields to be a marker

    Args:
        data (dict): Dictionary to be tested.

    Returns:
        Boolean, whether dictionary has necessary keys with a list has the value
    """
    keys = list(data.keys())
    if len(keys) == 0:
        return False
    else:
        need = ['Click X', 'Click Y', 'Width']
        for item in need:
            if item not in keys or not isinstance(data[item], list):
                return False
    return True


def marker_find(data, res):
    """
    Recursively examines dictionary and finds marker click coordinates and transect widths.

    Args:
        data (dict): Dictionary to examine
        res (list): Empty list to fill with marker click coordinates and transect widths

    Returns:
        Nested List. A list containing a list for each marker which each contains three lists:
        click X coords, click y coords, and the transect width for each click point in the marker.
        If no qualifying data was found returns empty list. If duplicate data is found (ex: multiple
        variables in a file) only returns one instance of marker data.
    """
    for key in list(data.keys()):
        if key[0:6] == 'Marker':
            if correct_test(data[key]):  # Marker dict has necessary fields
                if len(res) == 0:  # If res empty, always add marker data
                    res.append([data[key]['Click X'], data[key]['Click Y'], data[key]['Width']])
                else:  # If res not empty, ensure found marker data isn't already in res
                    new = True
                    for item in res:
                        l1 = data[key]['Click X']
                        l2 = item[0]
                        if len(l1) == len(l2) and len(l1) == sum([1 for i, j in zip(l1, l2) if i == j]):
                            new = False
                    if new:
                        res.append([data[key]['Click X'], data[key]['Click Y'], data[key]['Width']])
        else:
            if type(data[key]) is dict:  # Can still go further in nested dictionary tree
                marker_find(data[key], res)
            else:
                return res
    return res


class MultiMarker(ui.widget.Widget):
    """
    Transect marker tool widget.

    Created when Transect Marker button is selected. From there on this object manages the creation,
    modification, and data packaging of markers. Manages the uploading of previous projects
    into the viewer.

    Attributes:
        m_on (bool): Whether there are any markers active
        upload_fail (bool): If anything has gone wrong in the project uploading process
        home: Reference to root :class:`nccut.homescreen.HomeScreen` instance
        dbtn: RoundedButton, Plot button to activate PlotPopup
        dragging (bool): Whether viewer is in dragging mode
        width_w: :class:`nccut.markerwidth.MarkerWidth` widget to allow for adjustable marker widths
        clicks (int): Number of clicks made by user. Does not decrease when points are deleted
            unless all points are deleted in which case it goes back to zero.
        up_btn: RoundedButton, Upload button for uploading a past project
        nbtn: RoundedButton, New marker button
        plotting: :class:`nccut.plotpopup.PlotPopup`, reference to plotting menu when opened
        curr_width (int): Current marker width being used. Used to initialize width of new markers.
    """
    def __init__(self, home, **kwargs):
        """
        Defines sidebar elements and initializes widget

        Args:
            home: Reference to root :class:`nccut.homescreen.HomeScreen` instance
        """
        super(MultiMarker, self).__init__(**kwargs)
        self.m_on = False
        self.upload_fail = False
        self.home = home
        self.dbtn = func.RoundedButton(text="Plot", size_hint=(1, 0.1), font_size=self.home.font)
        self.dbtn.bind(on_press=lambda x: self.gather_popup())
        self.dragging = False
        self.width_w = MarkerWidth(self, size_hint=(1, 0.1))
        self.clicks = 0
        self.plotting = None
        self.curr_width = 40

        # Upload Button
        self.upbtn = func.RoundedButton(text="Upload Project", size_hint=(1, 0.1), font_size=self.home.font)
        self.upbtn.bind(on_press=lambda x: self.upload_pop())
        self.home.ids.sidebar.add_widget(self.upbtn, 1)

        # New Line Button
        self.nbtn = func.RoundedButton(text="New Line", size_hint=(1, 0.1), font_size=self.home.font)

        self.nbtn.bind(on_press=lambda x: self.new_line())
        self.home.ids.sidebar.add_widget(self.nbtn, 1)

    def font_adapt(self, font):
        """
        Updates font of sidebar elements and plotting menu if loaded.
        Args:
            font (float): New font size
        """
        self.dbtn.font_size = font
        self.upbtn.font_size = font
        self.nbtn.font_size = font
        self.width_w.font_adapt(font)
        if self.plotting:
            self.plotting.font_adapt(font)

    def update_l_col(self, color):
        """
        Asks each marker to update their line color

        Args:
            color (str): New color value: 'Blue', 'Green' or 'Orange'
        """
        for m in self.children:
            m.update_l_col(color)

    def update_c_size(self, value):
        """
       Asks each marker to update their circle size

       Args:
           value (float): New circle size
       """
        for m in self.children:
            m.update_c_size(value)

    def change_dragging(self, val):
        """
        Change whether in dragging mode or not.

        Args:
            val (bool): Whether in dragging mode or not.
        """
        self.dragging = val

    def upload_pop(self):
        """
        Opens popup to ask for name of project file user wishes to upload.
        """
        content = ui.boxlayout.BoxLayout(orientation='horizontal')
        popup = Popup(title="File Name", content=content, size_hint=(0.5, 0.15))
        txt = TextInput(size_hint=(0.7, 1), hint_text="Enter File Name")
        content.add_widget(txt)
        go = Button(text="Ok", size_hint=(0.1, 1))
        go.bind(on_release=lambda x: self.check_file(txt.text, popup))
        close = Button(text="Close", size_hint=(0.2, 1))
        close.bind(on_press=popup.dismiss)
        content.add_widget(go)
        content.add_widget(close)
        popup.open()

    def check_file(self, file, popup):
        """
        Checks is given file name is a properly formatted project file. If it is it uploads
        file. If not, closes popups and shows error message.

        Args:
            file (str): File path
            popup: kivy.uix.popup.Popup, File name input popup (so can close if file invalid)
        """
        if exists(file):
            if file[-5:] == ".json":
                data = json.load(open(file))
                found = marker_find(data, [])
                if len(found) >= 1:
                    popup.dismiss()
                    self.upload_data(found)
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

    def upload_fail_alert(self):
        """
        Indicate upload has failed
        """
        self.upload_fail = True

    def upload_data(self, points):
        """
        Loads markers from project file.

        Adds markers by 'clicking' the points in the file with the marker width denoted by the file

        Args:
            points: Properly formatted nested list from :class:`nccut.multimarker.marker_find()` function.
        """
        self.upload_fail = False
        if len(self.children) != 0:  # If markers already exist in viewer
            self.children[0].stop_drawing()
            if self.children[0].clicks < 2:  # If any existing markers are incomplete, remove them
                if self.children[0].clicks == 1:
                    self.children[0].del_point()
                self.remove_widget(self.children[0])
        for m in range(0, len(points)):
            marker = Marker(home=self.home, width=self.curr_width)
            clicks = tuple(zip(points[m][0], points[m][1], points[m][2]))
            marker.upload_mode(True)
            self.add_widget(marker)
            for i in clicks:
                touch = Click(i[0], i[1])
                marker.t_width = i[2]
                marker.on_touch_down(touch)
                self.clicks += 1
            marker.upload_mode(False)
            if self.upload_fail:  # If upload goes wrong, stop and undo everything
                self.undo_upload(m)
                return
        self.new_line()

    def undo_upload(self, markers):
        """
        Remove any previous markers that had been uploaded if upload fails

        Args:
            markers (int): Number of markers added so far
        """
        for m in range(0, markers + 1):
            Window.unbind(mouse_pos=self.children[0].draw_line)
            self.remove_widget(self.children[0])
        if len(self.children) == 0:
            # Remove sidebar buttons if deleted marker was the only marker
            self.clicks = 0
            if self.dbtn in self.home.display.current:
                self.home.display.current.remove(self.dbtn)
            if self.width_w in self.home.display.current:
                self.home.display.current.remove(self.width_w)
            if self.dragging:
                self.home.display.drag_mode()
            self.new_line()
        content = Label(text="Project File Markers out of Bounds")
        popup = Popup(title="Error", content=content, size_hint=(0.5, 0.15))
        popup.open()

    def update_width(self, num):
        """
        Update width of active marker.

        Args:
            num (int): New width value
        """
        self.curr_width = num
        self.children[0].update_width(num)

    def del_line(self):
        """
        Delete most recent marker with some safeguards.

        If only one marker on screen, delete but add new marker and remove sidebar elements.
        Otherwise delete current marker and go to previous. If no markers are on screen nothing
        happens.
        """
        if len(self.children) == 0:
            # If no markers on screen do nothing
            return
        Window.unbind(mouse_pos=self.children[0].draw_line)
        self.remove_widget(self.children[0])
        if len(self.children) == 0:
            # Remove sidebar buttons if deleted marker was the only marker
            self.clicks = 0
            if self.dbtn in self.home.display.current:
                self.home.display.current.remove(self.dbtn)
            if self.width_w in self.home.display.current:
                self.home.display.current.remove(self.width_w)
            self.new_line()

    def del_point(self):
        """
        Delete most recently clicked point with some safeguards.

        If no markers are on screen does nothing. If only one marker exists and no points have been clicked,
        does nothing. If more than one marker exists and no points have been clicked on most recent marker,
        Deletes most recent marker and then deletes last point of previous marker. Any other conditions
        simply deletes last clicked point.
        """
        if len(self.children) == 0:
            # If no markers on screen do nothing
            return
        elif self.children[0].clicks == 0:
            if len(self.children) > 1:
                # If no clicks on current marker and not the only marker delete current marker
                self.remove_widget(self.children[0])
            else:
                return
        # Delete point from current marker
        self.children[0].del_point()

    def new_line(self):
        """
        Creates a new marker if not in dragging or editing mode and current marker has at least two clicks.
        """
        if not self.dragging or self.home.display.editing:
            if len(self.children) == 0 or self.children[0].clicks >= 2:
                if len(self.children) != 0:
                    self.children[0].stop_drawing()
                m = Marker(home=self.home, width=self.curr_width)
                self.add_widget(m)

    def gather_popup(self):
        """
        Gather data from markers and call for :class:`nccut.plotpopup.PlotPopup`
        """
        frames = {}
        c = 1
        for i in reversed(self.children):
            if i.clicks > 0:  # Ignore empty markers
                data = {}
                data['Click X'], data['Click Y'], data['Width'] = map(list, zip(*i.points))
                count = 1
                for j in i.base.lines:
                    data["Cut " + str(count)] = j.line.points
                    count += 1
                frames["Marker " + str(c)] = data
                c += 1
        self.plotting = PlotPopup(frames, self.home, self.home.display.config)

    def on_touch_down(self, touch):
        """
        Manages when sidebar elements are added to sidebar and clears them as needed.

        Args:
            touch: MouseMotionEvent, see kivy docs for details
        """
        if not self.dragging:
            if self.home.ids.view.collide_point(*self.home.ids.view.to_widget(*self.to_window(*touch.pos))):
                self.clicks += 1
                if self.clicks >= 1 and self.width_w.parent is None:
                    self.home.ids.sidebar.add_widget(self.width_w, 1)
                if self.clicks >= 2 and self.dbtn.parent is None:
                    self.home.ids.sidebar.add_widget(self.dbtn, 1)
                # If no current marker, create marker. Otherwise, pass touch to current marker.
                if not self.m_on:
                    self.new_line()
                    self.m_on = True
                self.children[0].on_touch_down(touch)
