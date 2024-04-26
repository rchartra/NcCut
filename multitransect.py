"""
Class for multiple transect tool
"""
import kivy.uix as ui
from kivy.uix.button import Button
from plotpopup import PlotPopup
from singletransect import SingleTransect
import functions as func
from kivy.core.window import Window


class MultiTransect(ui.widget.Widget):
    # Creates, stores, and manages multiple transects
    def __init__(self, home, **kwargs):
        super(MultiTransect, self).__init__(**kwargs)
        self.lines = []
        self.clicks = 0
        self.mpoints = 0
        self.home = home
        self.p_btn = func.RoundedButton(text="Plot", size_hint=(1, 0.1), font_size=self.home.font)
        self.p_btn.bind(on_press=lambda x: self.popup())
        self.dragging = False

    def font_adapt(self, font):
        self.p_btn.font_size = font

    def del_line(self):
        # Delete all clicked points in most recent line
        for i in range(self.clicks):
            self.del_point()

    def del_point(self):
        # Delete most recent clicked point
        if len(self.lines) == 0:
            return
        elif self.children[0].circles == 1:
            # Case where point is beginning of a transect
            Window.unbind(mouse_pos=self.children[0].draw_line)
            self.remove_widget(self.children[0])
            self.lines = self.lines[:-1]
            # Add plot button to sidebar
            self.home.img.current.insert(0, self.p_btn)
        elif self.children[0].circles == 2:
            # Case where point is end of a transect
            self.children[0].del_point()
            if self.p_btn in self.home.img.current:
                # Remove plot button from sidebar
                self.home.img.current.remove(self.p_btn)
        if self.clicks == 2:
            self.clicks = 0
        self.clicks += 1

    def change_dragging(self, val):
        self.dragging = val

    def marker_points(self, plist):
        # When used as base by marker widget, gets users clicking points for download
        self.mpoints = plist

    def popup(self):
        # Gathers input and calls for popup
        if self.mpoints == 0:
            data = {}
        else:
            x, y, w = zip(*self.mpoints)
            data = {"Click X": list(x), "Click Y": list(y), "Width": list(w)}
        count = 1
        for i in self.lines:
            data["Cut " + str(count)] = i.line.points
            count += 1
        # Open plotting popup
        PlotPopup({"Multi": data}, self.home)

    def on_touch_down(self, touch):
        # Transect creation and display code
        # Determines what to do based on which of 3 click stages the user is in

        if not self.dragging:
            if self.home.ids.view.collide_point(*self.home.ids.view.to_widget(*self.to_window(*touch.pos))):
                if self.clicks == 2:
                    # Clean up download button from previous cycle
                    self.clicks = 0
                    self.home.ids.sidebar.remove_widget(self.p_btn)
                if self.clicks == 0:
                    # Begins a new transect
                    x = SingleTransect(home=self.home)

                    self.add_widget(x)
                    self.lines.append(x)
                if [touch.x, touch.y] == self.lines[-1].line.points:
                    return
                # Single transect manages the line and dots graphics
                self.lines[-1].on_touch_down(touch)
                if self.clicks == 1:
                    # If clicked same point as before, do nothing
                    # Finishes a transect, displays download button
                    if self.p_btn not in self.home.ids.sidebar.children:
                        self.home.ids.sidebar.add_widget(self.p_btn, 1)
                self.clicks += 1
