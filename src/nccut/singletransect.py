"""
Graphics for a single transect whether drawn by user or used to hold data by marker tool.

Draws circle at each user click point. When one point has been clicked, draws line from that
point to user cursor.
"""

import kivy.uix as ui
from kivy.graphics import Color, Ellipse, Line
from kivy.metrics import dp
from kivy.uix.label import Label
from kivy.core.window import Window


class SingleTransect(ui.widget.Widget):
    """
    Graphics for a single transect whether drawn by user or used to hold data by marker tool.

    Draws circle at each user click point. When one point has been clicked, draws line from that
    point to user cursor.

    Attributes:
        line: Line object which holds endpoint data
        c1: Ellipse object for first point clicked
        c2: Ellipse object for second point clicked
        number: Label, reference to number label
        circles (int): Number of circles drawn, ie points clicked by user
        home: Reference to root :class:`nccut.homescreen.HomeScreen` instance
        size: 2 element array of ints, Size of widget
        pos: 2 element array of ints, Position of widget
        l_color: kivy.graphics.Color, Color to use for graphics
        c_size (tuple): 2 element tuple of floats that defines size of circles and other graphics
        line_width (float): Float, width of lines
    """
    def __init__(self, home, **kwargs):
        """
        Sets initial settings for transect according to attributes of HomeScreen root

        Args:
            home: Reference to root :class:`nccut.homescreen.HomeScreen` instance
        """
        super(SingleTransect, self).__init__(**kwargs)
        self.line = None
        self.c1 = None
        self.c2 = None
        self.number = None
        self.circles = 0
        self.home = home
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
        Updates the line color for the transect and redraws canvas elements

        Args:
            color (str): New color value: 'Blue', 'Green' or 'Orange'
        """
        if color == "Blue":
            self.l_color = Color(0.28, 0.62, 0.86)
        elif color == "Green":
            self.l_color = Color(0.39, 0.78, 0.47)
        elif color == "Orange":
            self.l_color = Color(0.74, 0.42, 0.13)
        graphics = [self.c1, self.c2, self.line]
        for g in graphics:
            if g:
                self.canvas.remove(g)
        self.canvas.add(self.l_color)
        for g in graphics:
            if g:
                self.canvas.add(g)

    def update_c_size(self, value):
        """
        Updates graphic sizes according to the new value.

        Args:
            value (float): New graphics size
        """
        self.line_width = dp(value / 5)
        self.line.width = self.line_width
        for c in [self.c1, self.c2]:
            if c:
                c.size = (dp(value), dp(value))
                c.pos = (c.pos[0] + self.c_size[0] / 2 - dp(value) / 2, c.pos[1] + self.c_size[1] / 2 - dp(value) / 2)
        self.number.font_size = dp(value) * 2
        self.number.pos = (self.number.pos[0] + self.c_size[0] - dp(value),
                           self.number.pos[1] + self.c_size[1] - dp(value))
        self.c_size = (dp(value), dp(value))

    def on_touch_down(self, touch):
        """
        Draws points and lines depending on which parts of the transect have already been drawn.

        Args:
            touch: MouseMotionEvent, see kivy docs for details
        """
        if self.home.ids.view.collide_point(*self.home.ids.view.to_widget(*self.to_window(*touch.pos))):
            if self.circles == 0:  # If first click, add number, one circle, and draw line between point and cursor
                self.circles += 1
                self.number = Label(text=str(len(self.parent.children)),
                                    pos=(touch.x + self.c_size[0], touch.y + self.c_size[0]),
                                    font_size=self.c_size[0] * 2)
                self.add_widget(self.number)
                with self.canvas:
                    # Add points and start line
                    Color(self.l_color.r, self.l_color.g, self.l_color.b)
                    self.line = Line(points=[], width=self.line_width, group='end')
                    self.c1 = Ellipse(pos=(touch.x - self.c_size[0] / 2, touch.y - self.c_size[1] / 2),
                                      size=self.c_size, group='start')
                    self.line.points = (touch.x, touch.y)
                # Bind line drawing to any time user mouse position changes
                Window.bind(mouse_pos=self.draw_line)

            elif self.circles == 1:  # If second click draw another circle and draws line between circles
                self.circles += 1
                if len(self.line.points) != 2:  # Stops drawing line between first circle and cursor
                    self.line.points.pop()
                    self.line.points.pop()
                if [touch.x, touch.y] == self.line.points:  # If clicked the same point as before, do nothing
                    return
                with self.canvas:  # Second circle and sets line between the two circles.
                    self.c2 = Ellipse(pos=(touch.x - self.c_size[0] / 2, touch.y - self.c_size[1] / 2),
                                      size=self.c_size, group='end')
                    self.line.points += (touch.x, touch.y)

    def draw_line(self, instance, pos):
        """
        When one point is clicked and user mouse is just hovering, continuously update line end point
        to be at mouse cursor

        Updates anytime cursor moves. Does not draw if tool in dragging mode or cursor not in viewing window.

        Args:
            instance: WindowSDL instance, current window loaded (not used by method)
            pos (tuple): 2 element tuple of floats, x and y coord of cursor position
        """
        if not self.parent.dragging:
            if self.home.ids.view.collide_point(*self.home.ids.view.to_widget(*pos)):
                mouse = self.to_widget(*pos)
                if self.size[0] >= mouse[0] >= 0 and self.size[1] >= mouse[1] >= 0:
                    # If cursor within image bounds
                    if self.circles == 1:
                        if len(self.line.points) != 2:
                            # If already drawn previously, remove end point
                            self.line.points.pop()
                            self.line.points.pop()
                        with self.canvas:

                            self.line.points += self.to_widget(pos[0], pos[1])
        else:
            # If in dragging mode, don't draw and erase line
            if self.parent.lines[-1] == self and self.circles == 1:
                with self.canvas:
                    self.line.points = self.line.points[0:2]

    def del_point(self):
        """
        Delete most recently clicked point and reset
        """
        self.canvas.remove_group('end')
        self.circles -= 1
        self.line.points = self.line.points[:2]
        self.canvas.add(self.line)
        Window.bind(mouse_pos=self.draw_line)
