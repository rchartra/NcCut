"""
Class for a singular transect
"""

import kivy.uix as ui
from kivy.graphics import Color, Ellipse, Line
from kivy.metrics import dp
from kivy.uix.label import Label
from kivy.core.window import Window


class SingleTransect(ui.widget.Widget):
    # Base code for any single transect
    def __init__(self, home, **kwargs):
        super(SingleTransect, self).__init__(**kwargs)
        self.line = Line()
        self.circles = 0
        self.home = home
        self.size = self.home.img.size
        self.pos = self.home.img.pos
        color = self.home.l_col
        if color == "Blue":
            self.l_color = Color(0.28, 0.62, 0.86)
        elif color == "Green":
            self.l_color = Color(0.39, 0.78, 0.47)
        else:
            self.l_color = Color(0.74, 0.42, 0.13)
        size = home.cir_size
        self.c_size = (dp(size), dp(size))
        self.line_width = dp(size / 5)

    def on_touch_down(self, touch):
        # Gathering touch coordinates and display line graphics
        if self.home.ids.view.collide_point(*self.home.ids.view.to_widget(*self.to_window(*touch.pos))):
            if self.circles == 0:
                # If first click
                self.circles += 1
                number = Label(text=str(len(self.parent.children)), pos=(touch.x, touch.y), font_size=self.c_size[0])
                self.add_widget(number)
                with self.canvas:
                    # Add points and start line
                    Color(self.l_color.r, self.l_color.g, self.l_color.b)
                    self.line = Line(points=[], width=self.line_width, group='end')
                    c1 = Ellipse(pos=(touch.x - self.c_size[0] / 2, touch.y - self.c_size[1] / 2),
                                 size=self.c_size, group='start')
                    self.line.points = (touch.x, touch.y)
                # Bind line drawing to any time user mouse position changes
                Window.bind(mouse_pos=self.draw_line)

            elif self.circles == 1:
                self.circles += 1
                if len(self.line.points) != 2:
                    # Remove end point of line (drawn when user mouse is just hovering around)
                    self.line.points.pop()
                    self.line.points.pop()
                if [touch.x, touch.y] == self.line.points:
                    # If clicked the same point as before, do nothing
                    return
                with self.canvas:
                    # Finish line
                    c2 = Ellipse(pos=(touch.x - self.c_size[0] / 2, touch.y - self.c_size[1] / 2),
                                 size=self.c_size, group='end')
                    self.line.points += (touch.x, touch.y)

    def draw_line(self, instance, pos):
        # When one point is clicked and user mouse is just hovering, continuously update line end point
        # to be at mouse cursor
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
            # If in dragging mode, don't draw
            if self.parent.lines[-1] == self and self.circles == 1:
                with self.canvas:
                    self.line.points = self.line.points[0:2]

    def del_point(self):
        # Delete most recently clicked point and reset
        self.canvas.remove_group('end')
        self.circles -= 1
        self.line.points = self.line.points[:2]
        self.canvas.add(self.line)
        Window.bind(mouse_pos=self.draw_line)
