# SPDX-FileCopyrightText: 2024 University of Washington
#
# SPDX-License-Identifier: BSD-3-Clause

"""
Singular marker widget.

Graphics and functionality of a singular marker created by the transect marker tool.
"""

import kivy.uix as ui
from kivy.metrics import dp
from kivy.graphics import Color, Ellipse, Line
from kivy.uix.label import Label
import math
import numpy as np
from kivy.core.window import Window
import nccut.functions as functions


class Marker(ui.widget.Widget):
    """
    Singular transect marker widget.

    Graphics and functionality of a singular marker created by the transect marker tool.
    Determines endpoints of where transects should be made orthogonally to the user marked
    out line, and then stores the transects.

    Attributes:
        clicks (int): Number of clicks user has made. Decreases when points are deleted.
        points (list): List of Tuples, For each click user makes: (X-coord, Y-coord, t_width).
        t_width (int): Current width in pixels of orthogonal transects
        home: Reference to root :class:`nccut.homescreen.HomeScreen` instance
        transects (list): List of transects made
        curr_line: kivy.graphics.Line, Line between cursor and last clicked
        number: kivy.uix.label.Label, Reference to the number label
        size: 2 element array of ints, Size of widget
        pos: 2 element array of ints, Position of widget
        l_color: kivy.graphics.Color, Color to use for graphics
        c_size: 2 element tuple of floats that defines size of circles
        line_width (float): Width of lines
    """
    def __init__(self, home, width, **kwargs):
        """
        Sets initial settings and initializes object.

        Args:
            home: Reference to root :class:`nccut.homescreen.HomeScreen` instance
            width (int): Initial transect width to use.
        """
        super(Marker, self).__init__(**kwargs)
        self.clicks = 0
        self.points = []
        self.t_width = width
        self.uploaded = False
        self.home = home
        self.transects = []
        self.curr_line = Line()
        self.number = None
        self.size = self.home.display.size
        self.pos = self.home.display.pos
        color = self.home.display.l_col
        if color == "Blue":
            self.l_color = Color(0.28, 0.62, 0.86)
        elif color == "Green":
            self.l_color = Color(0.39, 0.78, 0.47)
        elif color == "Orange":
            self.l_color = Color(0.74, 0.42, 0.13)
        size = self.home.display.cir_size
        self.c_size = (dp(size), dp(size))
        self.line_width = dp(size / 5)

    def update_l_col(self, color):
        """
        Update the line color and redraw all items on canvas.

        Args:
            color (str): New line color to use
        """
        if color == "Blue":
            self.l_color = Color(0.28, 0.62, 0.86)
        elif color == "Green":
            self.l_color = Color(0.39, 0.78, 0.47)
        elif color == "Orange":
            self.l_color = Color(0.74, 0.42, 0.13)
        groups = []
        for c in range(1, self.clicks + 1):
            group = self.canvas.get_group(str(c))
            groups.append(group)
        self.canvas.clear()
        self.remove_widget(self.number)
        self.canvas.add(self.l_color)
        for g in groups:
            for i in g:
                self.canvas.add(i)
        self.canvas.add(self.curr_line)
        if self.clicks > 0:
            self.add_widget(self.number)

    def update_c_size(self, value):
        """
        Updates graphic sizes according to the new circle size value.

        Args:
            value (float): New graphics size
        """
        self.line_width = dp(value / 5)
        for c in range(1, self.clicks + 1):
            group = self.canvas.get_group(str(c))
            for i in group:
                if isinstance(i, Ellipse):
                    i.size = (dp(value), dp(value))
                    i.pos = (i.pos[0] + self.c_size[0] / 2 - dp(value) / 2,
                             i.pos[1] + self.c_size[1] / 2 - dp(value) / 2)
                elif isinstance(i, Line):
                    i.width = self.line_width
        if self.clicks > 0:
            self.number.font_size = dp(value) * 2
        self.curr_line.width = self.line_width
        self.c_size = (dp(value), dp(value))

    def update_width(self, width):
        """
        Update t_width to change width for next transect made.

        Args:
            width (int): New width to use
        """
        self.t_width = width
        if len(self.points) == 1:  # Update extra width entry at start of list so avg can be taken
            self.points[0] = (self.points[0][0], self.points[0][1], width)

    def upload_mode(self, val):
        """
        Update whether in upload mode or not

        Args:
            val (bool): Whether in upload mode or not
        """
        self.uploaded = val

    def get_orthogonal(self, line):
        """
        Get a line orthogonal to line drawn by user to use as transect.

        Args:
            line: kivy.graphics.Line, line between two last clicked points

        Returns:
            4 element array of floats: Coordinates of the two endpoints of the centered
            orthogonal line with length t_width.
        """
        xyswap = False
        line = line.points

        if line[0] > line[2]:  # Always read from left point to right
            line = [line[2], line[3], line[0], line[1]]

        # Calculate line slope ensuring never dividing by zero
        if line[2] - line[0] == 0:
            m = (line[3] - line[1]) / .001
        else:
            m = (line[3] - line[1]) / (line[2] - line[0])

        # Get orthogonal slope
        if m == 0:
            m = -1 / .001
        else:
            m = -1 / m

        if abs(math.atan(m)) > (math.pi / 4):  # If angle of line is > 45 degrees will swap x and y to increase accuracy

            xyswap = True
            line = [line[1], line[0], line[3], line[2]]
            m = 1 / m

        # Find midpoint
        mid = (line[0] + (line[2] - line[0]) / 2, line[1] + (line[3] - line[1]) / 2)
        # Calculate orthogonal line points
        b = mid[1] - m * mid[0]
        xarr = np.arange(int(np.floor(mid[0] - self.t_width / 2)), int(np.floor(mid[0] + self.t_width / 2 + 1)),
                         dtype=float)
        yarr = (xarr * m + b).tolist()
        xarr = xarr.tolist()

        # Draw points at ends of transect
        with self.canvas:
            Color(self.l_color.r, self.l_color.g, self.l_color.b)
            coords = [xarr[0], yarr[0], xarr[-1], yarr[-1]]
            if xyswap:
                coords = [yarr[0], xarr[0], yarr[-1], xarr[-1]]
            Ellipse(pos=(coords[0] - self.c_size[0] / 2, coords[1] - self.c_size[1] / 2),
                    size=self.c_size, group=str(self.clicks))
            Ellipse(pos=(coords[2] - self.c_size[0] / 2, coords[3] - self.c_size[1] / 2),
                    size=self.c_size, group=str(self.clicks))
        return coords

    def del_point(self):
        """
        Remove most recent point, line, and transect points.

        Graphics are grouped by the number of clicks made when they were created for easier deletion.
        """
        if self.clicks != 1:
            self.transects = self.transects[:-1]
        else:
            # Remove plot and width buttons from sidebar if last point of the marker
            if self.parent.dbtn in self.home.display.tool_action_widgets:
                self.home.display.remove_from_tool_action_widgets(self.parent.dbtn)
            if self.parent.width_w in self.home.display.tool_action_widgets:
                self.home.display.remove_from_tool_action_widgets(self.parent.width_w)
            self.remove_widget(self.children[0])
            # Stop drawing line between last point and cursor
            Window.unbind(mouse_pos=self.draw_line)
        self.points.remove(self.points[-1])
        self.canvas.remove_group(str(self.clicks))
        self.canvas.remove_group(str(self.clicks + 1))
        self.clicks -= 1

    def on_touch_down(self, touch):
        """
        On user click draws line, endpoints and orthogonal points.

        Args:
            touch: MouseMotionEvent, see kivy docs for details
        """
        # Draws marker line and points.
        proceed = False
        if self.uploaded:  # If being uploaded, just needs to be within image bounds
            if touch.pos[0] < self.size[0] and touch.pos[1] < self.size[1]:
                proceed = True
            else:
                self.parent.upload_fail_alert()  # Upload failed
        elif self.home.ids.view.collide_point(*self.home.ids.view.to_widget(*self.to_window(*touch.pos))):
            proceed = True  # If being clicked, must also be within viewing window
        if proceed:
            par = self.home.display.children[0].children[-2]
            self.clicks += 1
            with self.canvas:
                # Always adds point when clicked
                Color(self.l_color.r, self.l_color.g, self.l_color.b)
                Ellipse(pos=(touch.x - self.c_size[0] / 2, touch.y - self.c_size[1] / 2),
                        size=self.c_size, group=str(self.clicks))
                self.points.append((touch.x, touch.y, self.t_width))
                self.curr_line = Line(points=[], width=self.line_width, group=str(self.clicks + 1))
            # Draw line between last point and cursor whenever cursor position changes
            Window.bind(mouse_pos=self.draw_line)
            if self.clicks != 1:
                # If 2nd or more click, create a line inbetween click points
                with self.canvas:
                    Color(self.l_color.r, self.l_color.g, self.l_color.b)
                    line = Line(points=[self.points[-2][0:2], self.points[-1][0:2]],
                                width=self.line_width, group=str(self.clicks))
                # Stores orthogonal line
                coords = self.get_orthogonal(line)
                if self.in_bounds(coords):
                    # Check if orthogonal points are within image bounds
                    self.transects.append(Line(points=coords, width=self.line_width))
                else:
                    # Undo actions and alert user or parent
                    self.canvas.remove_group(str(self.clicks))
                    self.canvas.remove(self.curr_line)
                    self.clicks -= 1
                    self.points = self.points[:-1]
                    if self.uploaded:
                        self.parent.upload_fail_alert()
                    else:
                        functions.alert("Orthogonal point out of bounds", self.home)

            else:
                # If first click, adds marker number
                self.number = Label(text=str(len(par.children)), pos=(touch.x, touch.y), font_size=self.c_size[0] * 2)
                self.add_widget(self.number)

    def draw_line(self, instance, pos):
        """
        Draw line from most recent click point to user cursor.

        Updates anytime cursor moves. Does not draw if not current marker being drawn or if tool
        in dragging mode. Also won't draw if marker was uploaded and it was final marker.

        Args:
            instance: WindowSDL instance, current window loaded (not used by method)
            pos (tuple): 2 element tuple of floats, x and y coord of cursor position
        """
        if self.parent.children[0] == self and not self.parent.dragging:
            if self.home.ids.view.collide_point(*self.home.ids.view.to_widget(*pos)):
                mouse = self.to_widget(*pos)
                if self.size[0] >= mouse[0] >= 0 and self.size[1] >= mouse[1] >= 0:
                    with self.canvas:
                        Color(self.l_color.r, self.l_color.g, self.l_color.b)
                        self.curr_line.points = [self.points[-1][0:2], self.to_widget(pos[0], pos[1])]
        else:
            # Don't draw if not current marker or in dragging mode
            self.stop_drawing()

    def stop_drawing(self):
        """
        Remove line from most recent point to cursor.
        """
        with self.canvas:
            Color(self.l_color.r, self.l_color.g, self.l_color.b)
            self.curr_line.points = self.curr_line.points[0:2]

    def in_bounds(self, points):
        """
        Determine if points are within bounds of image.

        Args:
            points (list): List of 4 floats, X,Y coords of the two endpoints: [X1, Y1, X2, Y2]
        Returns:
            Boolean whether both endpoints are within image bounds
        """
        dots = [points[0:2], points[2:4]]
        for d in dots:
            if min(d) < 0 or any([i[0] > i[1] for i in list(zip(d, self.size))]):
                return False
        return True
