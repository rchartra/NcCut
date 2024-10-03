"""
Singular chain widget.

Graphics and functionality of a singular chain created by the transect chain tool.
"""

import kivy.uix as ui
from kivy.metrics import dp
from kivy.graphics import Color, Ellipse, Line
from kivy.uix.label import Label
from kivy.core.window import Window


class Chain(ui.widget.Widget):
    """
    Singular transect chain widget.

    Graphics and functionality of a singular chain created by the transect chain tool. Draws point on each user click
    and connects points with a line creating a chain of transects.

    Attributes:
        clicks (int): Number of clicks user has made. Decreases when points are deleted.
        points (list): List of Tuples, For each click user makes: (X-coord, Y-coord, t_width).
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
    def __init__(self, home, **kwargs):
        """
        Sets initial settings and initializes object.

        Args:
            home: Reference to root :class:`nccut.homescreen.HomeScreen` instance
        """
        super(Chain, self).__init__(**kwargs)
        self.clicks = 0
        self.points = []
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

    def del_point(self):
        """
        Remove most recent point, line, and transect points.

        Graphics are grouped by the number of clicks made when they were created for easier deletion.
        """
        if self.clicks != 1:
            self.transects = self.transects[:-1]
        else:
            # Remove plot buttons from sidebar if last point of the chain
            if self.parent.dbtn in self.home.display.tool_action_widgets:
                self.home.display.remove_from_tool_action_widgets(self.parent.dbtn)
            self.remove_widget(self.children[0])
            # Stop drawing line between last point and cursor
            Window.unbind(mouse_pos=self.draw_line)
        self.points.remove(self.points[-1])
        self.canvas.remove_group(str(self.clicks))
        self.canvas.remove_group(str(self.clicks + 1))
        self.clicks -= 1

    def on_touch_down(self, touch):
        """
        On user click draws line and endpoints.

        Args:
            touch: MouseMotionEvent, see kivy docs for details
        """
        # Draws chain line and points.
        if self.home.ids.view.collide_point(*self.home.ids.view.to_widget(*self.to_window(*touch.pos))):
            if self.clicks > 1 and (touch.x, touch.y) == self.points[-1]:
                return
            else:
                par = self.home.display.children[0].children[-2]
                self.clicks += 1
                with self.canvas:
                    # Always adds point when clicked
                    Color(self.l_color.r, self.l_color.g, self.l_color.b)
                    Ellipse(pos=(touch.x - self.c_size[0] / 2, touch.y - self.c_size[1] / 2),
                            size=self.c_size, group=str(self.clicks))
                    self.points.append((touch.x, touch.y))
                    self.curr_line = Line(points=[], width=self.line_width, group=str(self.clicks + 1))
                # Draw line between last point and cursor whenever cursor position changes
                Window.bind(mouse_pos=self.draw_line)
                if self.clicks > 1:
                    # If 2nd or more click, create a line inbetween click points
                    with self.canvas:
                        Color(self.l_color.r, self.l_color.g, self.l_color.b)
                        line = Line(points=[self.points[-2][0:2], self.points[-1][0:2]],
                                    width=self.line_width, group=str(self.clicks))
                    # Store line
                    self.transects.append(line)

                else:
                    # If first click, adds chain number
                    self.number = Label(text=str(len(par.children)), pos=(touch.x, touch.y), font_size=self.c_size[0] * 2)
                    self.add_widget(self.number)

    def draw_line(self, instance, pos):
        """
        Draw line from most recent click point to user cursor.

        Updates anytime cursor moves. Does not draw if not current chain being drawn or if tool
        in dragging mode.

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
            # Don't draw if not current chain or in dragging mode
            self.stop_drawing()

    def stop_drawing(self):
        """
        Remove line from most recent point to cursor.
        """
        with self.canvas:
            Color(self.l_color.r, self.l_color.g, self.l_color.b)
            self.curr_line.points = self.curr_line.points[0:2]
