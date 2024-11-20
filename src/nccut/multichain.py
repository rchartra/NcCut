"""
Transect chain tool widget.

Manages having multiple chains on screen at once.
"""

import kivy.uix as ui
from kivy.core.window import Window
from scipy.interpolate import CubicSpline
import nccut.functions as func
from nccut.chain import Chain


class MultiChain(ui.widget.Widget):
    """
    Transect chain tool widget.

    Created when Transect Chain button is selected. From there on this object manages the creation,
    modification, and data packaging of chains.

    Attributes:
        c_on (bool): Whether there are any chains active
        home: Reference to root :class:`nccut.homescreen.HomeScreen` instance
        dbtn: RoundedButton, Plot button to activate PlotPopup
        dragging (bool): Whether viewer is in dragging mode
        clicks (int): Number of clicks made by user. Does not decrease when points are deleted
            unless all points are deleted in which case it goes back to zero.
        nbtn: RoundedButton, New chain button
    """
    def __init__(self, home, b_height, **kwargs):
        """
        Defines sidebar elements and initializes widget

        Args:
            home: Reference to root :class:`nccut.homescreen.HomeScreen` instance
            b_height: Height for buttons in sidebar according to font size
        """
        super(MultiChain, self).__init__(**kwargs)
        self.c_on = False
        self.home = home
        self.dbtn = func.RoundedButton(text="Plot", size_hint_y=None, height=b_height, font_size=self.home.font)
        self.dbtn.bind(on_press=lambda x: self.gather_popup())
        self.dragging = False
        self.clicks = 0

        # New Chain Button
        self.nbtn = func.RoundedButton(text="New Chain", size_hint_y=None, height=b_height, font_size=self.home.font)

        self.nbtn.bind(on_press=lambda x: self.new_chain())
        self.home.display.add_to_sidebar([self.nbtn])

    def font_adapt(self, font):
        """
        Updates font of sidebar elements.
        Args:
            font (float): New font size
        """
        self.dbtn.font_size = font
        self.nbtn.font_size = font

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

    def del_line(self):
        """
        Delete most recent chain with some safeguards.

        If only one chain on screen, delete but add new chain and remove sidebar elements.
        Otherwise delete current chain and go to previous. If no chains are on screen nothing
        happens.
        """
        if len(self.children) == 0:
            # If no chains on screen do nothing
            return
        Window.unbind(mouse_pos=self.children[0].draw_line)
        self.remove_widget(self.children[0])
        if len(self.children) == 0:
            # Remove sidebar buttons if deleted chain was the only chain
            self.clicks = 0
            if self.dbtn in self.home.display.tool_action_widgets:
                self.home.display.remove_from_tool_action_widgets(self.dbtn)
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
            if self.dbtn in self.home.display.tool_action_widgets:
                self.home.display.remove_from_tool_action_widgets(self.dbtn)
            if len(self.children) > 1:
                # If no clicks on current chain and not the only chain delete current chain
                self.remove_widget(self.children[0])
            else:
                return
        # Delete point from current chain
        self.children[0].del_point()

    def new_chain(self):
        """
        Creates a new chain if not in dragging or editing mode and current chain has at least two clicks.
        """
        if not self.dragging or self.home.display.editing:
            if len(self.children) == 0 or self.children[0].clicks >= 2:
                if len(self.children) != 0:
                    self.children[0].stop_drawing()
                c = Chain(home=self.home)
                self.add_widget(c)

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
            x = config["netcdf"]["data"].coords[config["netcdf"]["x"]].data
            y = config["netcdf"]["data"].coords[config["netcdf"]["y"]].data
            try:
                x = x.astype(float)
                x_spline = CubicSpline(range(len(x)), x)

                y = y.astype(float)
                y_spline = CubicSpline(range(len(y)), y)
                x_name = config["netcdf"]["x"]
                y_name = config["netcdf"]["y"]
                nc_coords = True
            except ValueError:
                pass
        for i in reversed(self.children):
            if i.clicks > 0:  # Ignore empty chains
                data = {}
                cx, cy = map(list, zip(*i.points))
                if nc_coords:
                    cx = x_spline(cx)
                    cy = y_spline(cy)
                data['Click ' + str(x_name)], data['Click ' + str(y_name)] = cx, cy
                count = 1
                for j in i.transects:
                    data["Cut " + str(count)] = j.points
                    count += 1
                frames["Chain " + str(c)] = data
                c += 1
        self.home.plot_popup.run(frames, self.home, self.home.display.config)

    def on_touch_down(self, touch):
        """
        Manages when sidebar elements are added to sidebar and clears them as needed. If click is a right click and not
        the first click creates new marker.

        Args:
            touch: MouseMotionEvent, see kivy docs for details
        """
        if not self.dragging:
            if self.home.ids.view.collide_point(*self.home.ids.view.to_widget(*self.to_window(*touch.pos))):
                if self.clicks > 0 or touch.button == "left":
                    self.clicks += 1
                    if self.clicks >= 2 and self.dbtn.parent is None:
                        self.home.display.add_to_sidebar([self.dbtn])
                    # If no current chain, create chain. Otherwise, pass touch to current chain.
                    if not self.c_on:
                        self.new_chain()
                        self.c_on = True
                    self.children[0].on_touch_down(touch)
                    if touch.button == "right":
                        self.new_chain()
