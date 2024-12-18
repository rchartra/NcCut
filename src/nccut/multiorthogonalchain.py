# SPDX-FileCopyrightText: 2024 University of Washington
#
# SPDX-License-Identifier: BSD-3-Clause

"""
Orthogonal chain tool widget.

Manages having multiple orthogonal chains on screen at once and the uploading of previous projects.
"""

import kivy.uix as ui
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.core.window import Window
import json
from plyer import filechooser
from scipy.interpolate import CubicSpline
import numpy as np
import nccut.functions as func
from nccut.orthogonalchain import OrthogonalChain
from nccut.orthogonalchainwidth import OrthogonalChainWidth


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
        self.is_double_tap = False
        self.button = "left"


def correct_test(data, need):
    """
    Check if dictionary has necessary fields to be an orthogonal chain

    Args:
        data (dict): Dictionary to be tested.
        need (list): List of required fields to qualify as an orthogonal chain:
            ["Click <cord>", "Click <cord>", "Width"]

    Returns:
        Boolean, whether dictionary has necessary keys with a list has the value
    """
    keys = list(data.keys())
    if len(keys) == 0:
        return False
    else:
        for item in need:
            if item not in keys or not isinstance(data[item], list):
                return False
    return True


def orthogonal_chain_find(data, res, need):
    """
    Recursively examines dictionary and finds chain click coordinates and orthogonal transect widths.

    Args:
        data (dict): Dictionary to examine
        res (list): Empty list to fill with chain click coordinates and orthogonal transect widths
        need (list): List of required fields to qualify as an orthogonal chain:
            ["Click <cord>", "Click <cord>", "Width"]

    Returns:
        Nested List. A list containing a list for each orthogonal chain which each contains three lists:
        click X coords, click y coords, and the orthogonal transect width for each click point in the chain.
        If no qualifying data was found returns empty list. If duplicate data is found (ex: multiple
        variables in a file) only returns one instance of orthogonal chain data.
    """
    for key in list(data.keys()):
        if key[0:10] == 'Orthogonal':
            if correct_test(data[key], need):  # Orthogonal chain dict has necessary fields
                if len(res) == 0:  # If res empty, always add orthogonal chain data
                    res.append([data[key][need[0]], data[key][need[1]], data[key][need[2]]])
                else:  # If res not empty, ensure found orthogonal chain data isn't already in res
                    new = True
                    for item in res:
                        l1 = data[key][need[0]]
                        l2 = item[0]
                        if len(l1) == len(l2) and len(l1) == sum([1 for i, j in zip(l1, l2) if i == j]):
                            new = False
                    if new:
                        res.append([data[key][need[0]], data[key][need[1]], data[key][need[2]]])
        else:
            if type(data[key]) is dict:  # Can still go further in nested dictionary tree
                orthogonal_chain_find(data[key], res, need)
            else:
                return res
    return res


class MultiOrthogonalChain(ui.widget.Widget):
    """
    Orthogonal chain tool widget.

    Created when 'Orthogonal Chain' button is selected. From there on this object manages the creation,
    modification, and data packaging of orthogonal chains. Manages the uploading of previous projects
    into the viewer.

    Attributes:
        c_on (bool): Whether there are any chains active
        upload_fail (bool): If anything has gone wrong in the project uploading process
        home: Reference to root :class:`nccut.homescreen.HomeScreen` instance
        dbtn: RoundedButton, Plot button to activate :class:`nccut.plotpopup.PlotPopup`
        dragging (bool): Whether viewer is in dragging mode
        width_w: :class:`nccut.orthogonalchainwidth.OrthogonalChainWidth` widget to allow for adjustable orthogonal
            transect widths
        clicks (int): Number of clicks made by user. Decreases when points are deleted
        up_btn: RoundedButton, Upload button for uploading a past project
        nbtn: RoundedButton, New chain button
        curr_width (int): Current orthogonal transect width being used. Used to initialize width of new chains.
    """
    def __init__(self, home, t_width, b_height, **kwargs):
        """
        Defines sidebar elements and initializes widget

        Args:
            home: Reference to root :class:`nccut.homescreen.HomeScreen` instance
            t_width: Default orthogonal transect width in pixels
            b_height: Height for sidebar buttons based on font size
        """
        super(MultiOrthogonalChain, self).__init__(**kwargs)
        self.c_on = False
        self.upload_fail = False
        self.home = home
        self.dbtn = func.RoundedButton(text="Plot", size_hint_y=None, height=b_height, font_size=self.home.font)
        self.dbtn.bind(on_press=lambda x: self.gather_popup())
        self.dragging = False
        self.width_w = OrthogonalChainWidth(self, size_hint_y=None, height=b_height)
        self.clicks = 0
        self.curr_width = t_width

        # Upload Button
        self.upbtn = func.RoundedButton(text="Upload Project", size_hint_y=None, height=b_height,
                                        font_size=self.home.font)
        self.upbtn.bind(on_press=lambda x: self.upload_pop())

        # New Chain Button
        self.nbtn = func.RoundedButton(text="New Chain", size_hint_y=None, height=b_height, font_size=self.home.font)
        self.nbtn.bind(on_press=lambda x: self.new_chain())

        self.home.display.add_to_sidebar([self.upbtn, self.nbtn])

    def font_adapt(self, font):
        """
        Updates font of sidebar elements.

        Args:
            font (float): New font size
        """
        self.dbtn.font_size = font
        self.upbtn.font_size = font
        self.nbtn.font_size = font
        self.width_w.font_adapt(font)

    def update_l_col(self, color):
        """
        Asks each chain to update their line color

        Args:
            color (str): New color value: 'Blue', 'Green' or 'Orange'
        """
        for m in self.children:
            m.update_l_col(color)

    def update_c_size(self, value):
        """
       Asks each chain to update their circle size

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
        Opens native operating system file browser to allow user to select their project file
        """
        try:
            path = filechooser.open_file(filters=["*.json"])
            if path is not None and len(path) != 0:
                self.check_file(path[0])
        except Exception as e:
            func.alert_popup("Cannot upload project files at this time")

    def check_file(self, file):
        """
        Checks is given file name is a properly formatted project file. If it is it uploads
        file. If not, shows error message.

        Args:
            file (str): File path
        """
        data = json.load(open(file))
        config = self.home.display.config
        x_name = "X"
        y_name = "Y"
        nc_coords = False
        if list(config.keys())[0] == "netcdf":
            try:
                config["netcdf"]["data"].coords[config["netcdf"]["x"]].data.astype(float)
                config["netcdf"]["data"].coords[config["netcdf"]["y"]].data.astype(float)
                x_name = config["netcdf"]["x"]
                y_name = config["netcdf"]["y"]
                nc_coords = True
            except ValueError:
                pass
        found = orthogonal_chain_find(data, [], ["Click " + str(x_name), "Click " + str(y_name), "Width"])
        if len(found) >= 1:
            if nc_coords:
                found = self.convert_found_coords(found)
            self.upload_data(found)
        else:
            content = Label(text="JSON File is not a Project for this File")
            popup2 = Popup(title="Error", content=content, size_hint=(0.5, 0.15))
            popup2.open()

    def convert_found_coords(self, found):
        """
        If coordinates from uploaded project file came from the currently loaded NetCDF file convert the coordinates to
        pixel coordinates for plotting the chains on the viewer.

        Args:
            found: The found chains from the project file that have already been verified to have come from the current
                NetCDF file. A list containing a list for each chain which contains three lists: [X Coord List,
                Y Coord List, Width List]

        Returns:
            The original found list except the Click points have been converted to pixel coordinates
        """
        config = self.home.display.config
        for chain in found:
            for i, c in enumerate(["x", "y"]):
                coords = config["netcdf"]["data"].coords[config["netcdf"][c]].data.astype(float)
                c_spline = CubicSpline(coords, range(len(coords)))
                chain[i] = c_spline(chain[i]).tolist()
        return found

    def upload_fail_alert(self):
        """
        Indicate upload has failed
        """
        self.upload_fail = True

    def upload_data(self, points):
        """
        Loads chains from project file.

        Adds chains by 'clicking' the points in the file with the orthogonal transect width denoted by the file

        Args:
            points: Properly formatted nested list from :class:`nccut.multiorthogonalchain.orthogonal_chain_find()`
                function.
        """
        try:
            self.upload_fail = False
            if len(self.children) != 0:  # If chains already exist in viewer
                self.children[0].stop_drawing()
                if self.children[0].clicks < 2:  # If any existing chains are incomplete, remove them
                    if self.children[0].clicks == 1:
                        self.children[0].del_point()
                    self.remove_widget(self.children[0])
            for c in range(0, len(points)):
                chain = OrthogonalChain(home=self.home, width=self.curr_width)
                clicks = tuple(zip(points[c][0], points[c][1], points[c][2]))
                chain.upload_mode(True)
                self.add_widget(chain)
                for i in clicks:
                    touch = Click(i[0], i[1])
                    chain.t_width = i[2]
                    chain.on_touch_down(touch)
                    self.clicks += 1
                chain.upload_mode(False)
                if self.clicks >= 1 and self.width_w.parent is None:
                    self.home.display.add_to_sidebar([self.width_w])
                if self.clicks >= 2 and self.dbtn.parent is None:
                    self.home.display.add_to_sidebar([self.dbtn])
                if self.upload_fail:  # If upload goes wrong, stop and undo everything
                    self.undo_upload(c)
                    return
            self.new_chain()
        except Exception as error:
            func.alert_popup(str(error))

    def undo_upload(self, chains):
        """
        Remove any previous chains that had been uploaded if upload fails

        Args:
            chains (int): Number of chains added so far
        """
        for m in range(0, chains + 1):
            self.del_chain()
        if len(self.children) == 0:
            # Remove sidebar buttons if deleted chain was the only chain
            self.clicks = 0
            if self.dbtn in self.home.display.tool_action_widgets:
                self.home.display.remove_from_tool_action_widgets(self.dbtn)
            if self.width_w in self.home.display.tool_action_widgets:
                self.home.display.remove_from_tool_action_widgets(self.width_w)
            if self.dragging:
                self.home.display.drag_mode()
            self.new_chain()
        content = Label(text="Project File Chains out of Bounds")
        popup = Popup(title="Error", content=content, size_hint=(0.5, 0.15))
        popup.open()

    def update_width(self, num):
        """
        Update orthogonal transect width of active chain.

        Args:
            num (int): New width value
        """
        self.curr_width = num
        self.children[0].update_width(num)

    def del_chain(self):
        """
        Delete most recent chain with some safeguards.

        If only one chain on screen, delete but add new chain and remove sidebar elements.
        Otherwise delete current chain and go to previous. If no chain are on screen nothing
        happens.
        """
        if len(self.children) == 0:
            # If no chain on screen do nothing
            return
        Window.unbind(mouse_pos=self.children[0].draw_line)
        self.clicks -= self.children[0].clicks
        self.remove_widget(self.children[0])
        if len(self.children) == 0:
            # Remove sidebar buttons if deleted chain was the only chain
            if self.dbtn in self.home.display.tool_action_widgets:
                self.home.display.remove_from_tool_action_widgets(self.dbtn)
            if self.width_w in self.home.display.tool_action_widgets:
                self.home.display.remove_from_tool_action_widgets(self.width_w)
            self.new_chain()

    def del_point(self):
        """
        Delete most recently clicked point with some safeguards.

        If no chains are on screen does nothing. If only one chain exists and no points have been clicked,
        does nothing. If more than one chain exists and no points have been clicked on most recent chain,
        Deletes most recent chain and then deletes last point of previous chain. Any other conditions
        simply deletes last clicked point.
        """
        if len(self.children) == 0:
            # If no chains on screen do nothing
            return
        elif self.children[0].clicks == 0:
            if len(self.children) > 1:
                # If no clicks on current chain and not the only chain delete current chain
                self.remove_widget(self.children[0])
            else:
                return
        # Delete point from current chain
        self.children[0].del_point()
        self.clicks -= 1
        # Determine which buttons should be in sidebar
        if self.clicks == 1:
            self.home.display.remove_from_tool_action_widgets(self.dbtn)
        elif self.clicks == 0:
            self.home.display.remove_from_tool_action_widgets(self.width_w)

    def new_chain(self):
        """
        Creates a new chain if not in dragging or editing mode and current chain has at least two clicks.
        """
        if not self.dragging or self.home.display.editing:
            if len(self.children) == 0 or self.children[0].clicks >= 2:
                if len(self.children) != 0:
                    self.children[0].stop_drawing()
                m = OrthogonalChain(home=self.home, width=self.curr_width)
                self.add_widget(m)

    def gather_popup(self):
        """
        Gather data from chains and call for :class:`nccut.plotpopup.PlotPopup`
        """
        frames = {}
        c = 1
        nc_coords = False
        x_name = "X"
        y_name = "Y"
        if self.home.display.f_type == "netcdf":
            config = self.home.display.config
            x_coord = config["netcdf"]["data"].coords[config["netcdf"]["x"]].data
            y_coord = config["netcdf"]["data"].coords[config["netcdf"]["y"]].data
            try:
                x_coord = x_coord.astype(float)
                y_coord = y_coord.astype(float)
                x_pix = min(abs(x_coord[:-1] - x_coord[1:]))
                y_pix = min(abs(y_coord[:-1] - y_coord[1:]))
                x = np.arange(x_coord.min(), x_coord.max() + x_pix, x_pix)
                y = np.arange(y_coord.min(), y_coord.max() + y_pix, y_pix)

                x_spline = CubicSpline(range(len(x)), x)
                y_spline = CubicSpline(range(len(y)), y)

                x_name = config["netcdf"]["x"]
                y_name = config["netcdf"]["y"]
                nc_coords = True
            except ValueError:
                pass
        for i in reversed(self.children):
            if i.clicks > 0:  # Ignore empty chains
                data = {}
                cx, cy, w = map(list, zip(*i.points))
                if nc_coords:
                    cx = x_spline(cx).tolist()
                    cy = y_spline(cy).tolist()
                data['Click ' + str(x_name)], data['Click ' + str(y_name)], data['Width'] = cx, cy, w
                count = 1
                for j in i.transects:
                    data["Cut " + str(count)] = j.points
                    count += 1
                frames["Orthogonal Chain " + str(c)] = data
                c += 1
        self.home.plot_popup.run(frames, self.home, self.home.display.config)

    def on_touch_down(self, touch):
        """
        Manages when sidebar elements are added to sidebar and clears them as needed. If click is a right click and not
        the first click creates new chain.

        Args:
            touch: MouseMotionEvent, see kivy docs for details
        """
        if not self.dragging:
            if self.home.ids.view.collide_point(*self.home.ids.view.to_widget(*self.to_window(*touch.pos))):
                if self.clicks > 0 or touch.button == "left":
                    self.clicks += 1
                    if self.clicks >= 1 and self.width_w.parent is None:
                        self.home.display.add_to_sidebar([self.width_w])
                    if self.clicks >= 2 and self.dbtn.parent is None:
                        self.home.display.add_to_sidebar([self.dbtn])
                    # If no current chain, create chain. Otherwise, pass touch to current chain.
                    if not self.c_on:
                        self.new_chain()
                        self.c_on = True
                    self.children[0].on_touch_down(touch)
                    if touch.button == "right":
                        self.new_chain()
