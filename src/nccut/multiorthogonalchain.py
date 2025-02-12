# SPDX-FileCopyrightText: 2024 University of Washington
#
# SPDX-License-Identifier: BSD-3-Clause

"""
Orthogonal chain tool widget.

Manages having multiple orthogonal chains on screen at once and the loading of previous chain data.
"""

import kivy.uix as ui
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.core.window import Window
import json
from scipy.interpolate import CubicSpline
import numpy as np
import nccut.functions as func
from nccut.orthogonalchain import OrthogonalChain
from nccut.orthogonalchainwidth import OrthogonalChainWidth


class MultiOrthogonalChain(ui.widget.Widget):
    """
    Orthogonal chain tool widget.

    Created when 'Orthogonal Chain' button is selected. From there on this object manages the creation,
    modification, and data packaging of orthogonal chains. Manages the loading of previous chain data
    into the viewer.

    Attributes:
        c_on (bool): Whether there are any chains active
        load_fail (bool): If anything has gone wrong in the chain data loading process
        home: Reference to root :class:`nccut.homescreen.HomeScreen` instance
        d_btn: RoundedButton, Plot button to activate :class:`nccut.plotpopup.PlotPopup`
        dragging (bool): Whether viewer is in dragging mode
        width_btn: Button to open transect width adjustment popup
        clicks (int): Number of clicks made by user. Decreases when points are deleted
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
        self.load_fail = False
        self.home = home
        self.d_btn = func.RoundedButton(text="Plot Data", size_hint_y=None, height=b_height, font_size=self.home.font)
        self.d_btn.bind(on_press=lambda x: self.gather_popup())
        self.dragging = False
        self.width_btn = func.RoundedButton(text="Set Transect Width", size_hint_y=None, height=b_height,
                                            font_size=self.home.font)
        self.width_btn.bind(on_press=lambda x: self.width_pop())
        self.clicks = 0
        self.curr_width = t_width

    def font_adapt(self, font):
        """
        Updates font of sidebar elements.

        Args:
            font (float): New font size
        """
        self.d_btn.font_size = font
        self.width_btn.font_size = font

    def width_pop(self):
        """
        Opens transect width adjustment popup
        """
        OrthogonalChainWidth(self)

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
        if self.clicks >= 1 and self.width_btn.parent is None:
            self.home.display.add_to_sidebar(self.width_btn, 5)
        if self.clicks >= 2:
            if self.d_btn.parent is None:
                self.home.display.add_to_sidebar(self.d_btn)

    def change_dragging(self, val):
        """
        Change whether in dragging mode or not.

        Args:
            val (bool): Whether in dragging mode or not.
        """
        self.dragging = val

    def check_file(self, file):
        """
        Checks is given file name is a properly formatted chain data file. If it is it loads
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
        found = func.chain_find(data, [], ["Click " + str(x_name), "Click " + str(y_name), "Width"], "Orthogonal")
        if len(found) >= 1:
            if nc_coords:
                found = func.convert_found_coords(found, self.home.display.config)
            self.load_data(found)
        else:
            content = Label(text="JSON File is not an Orthogonal Chain Data File for This Dataset")
            popup2 = Popup(title="Error", content=content, size_hint=(0.5, 0.15))
            popup2.open()

    def load_fail_alert(self):
        """
        Indicate load has failed
        """
        self.load_fail = True

    def load_data(self, points):
        """
        Loads chains from chain data file.

        Adds chains by 'clicking' the points in the file with the orthogonal transect width denoted by the file

        Args:
            points: Properly formatted nested list from :class:`nccut.functions.chain_find()`
                function.
        """
        try:
            self.load_fail = False
            if len(self.children) != 0:  # If chains already exist in viewer
                self.children[0].stop_drawing()
                if self.children[0].clicks < 2:  # If any existing chains are incomplete, remove them
                    if self.children[0].clicks == 1:
                        self.children[0].del_point()
                    self.remove_widget(self.children[0])
            for c in range(0, len(points)):
                chain = OrthogonalChain(home=self.home, width=self.curr_width)
                clicks = tuple(zip(points[c][0], points[c][1], points[c][2]))
                chain.load_mode(True)
                self.add_widget(chain)
                for i in clicks:
                    touch = func.Click(i[0], i[1])
                    chain.t_width = i[2]
                    chain.on_touch_down(touch)
                    self.clicks += 1
                chain.load_mode(False)
                if self.clicks >= 1 and self.width_btn.parent is None:
                    self.home.display.add_to_sidebar(self.width_btn, 5)
                if self.clicks >= 2:
                    if self.d_btn.parent is None:
                        self.home.display.add_to_sidebar(self.d_btn)
                if self.load_fail:  # If load goes wrong, stop and undo everything
                    self.undo_load(c)
                    return
            self.new_chain()
        except Exception as error:
            func.alert_popup(str(error))

    def undo_load(self, chains):
        """
        Remove any previous chains that had been loaded if load fails

        Args:
            chains (int): Number of chains added so far
        """
        for m in range(0, chains + 1):
            self.del_chain()
        if len(self.children) == 0:
            # Remove sidebar buttons if deleted chain was the only chain
            self.clicks = 0
            if self.d_btn in self.home.display.tool_sb_widgets:
                self.home.display.remove_from_tool_sb_widgets(self.d_btn)
            if self.width_btn in self.home.display.tool_sb_widgets:
                self.home.display.remove_from_tool_sb_widgets(self.width_btn)
            if self.dragging:
                self.home.display.drag_mode()
            self.new_chain()
        content = Label(text="Data File Chains out of Bounds")
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
            if self.d_btn in self.home.display.tool_sb_widgets:
                self.home.display.remove_from_tool_sb_widgets(self.d_btn)
            if self.width_btn in self.home.display.tool_sb_widgets:
                self.home.display.remove_from_tool_sb_widgets(self.width_btn)
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
            if self.d_btn in self.home.display.tool_sb_widgets:
                self.home.display.remove_from_tool_sb_widgets(self.d_btn)
        elif self.clicks == 0 and self.width_btn in self.home.display.tool_sb_widgets:
            self.home.display.remove_from_tool_sb_widgets(self.width_btn)

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
                    if self.clicks >= 1 and self.width_btn.parent is None:
                        self.home.display.add_to_sidebar(self.width_btn, 5)
                    if self.clicks >= 2:
                        if self.d_btn.parent is None:
                            self.home.display.add_to_sidebar(self.d_btn)
                    # If no current chain, create chain. Otherwise, pass touch to current chain.
                    if not self.c_on:
                        self.new_chain()
                        self.c_on = True
                    self.children[0].on_touch_down(touch)
                    if touch.button == "right":
                        self.new_chain()
