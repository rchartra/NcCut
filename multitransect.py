"""
Class for multiple transect tool that manages any case where multiple single transects are needed.
"""
import kivy.uix as ui
from kivy.uix.button import Button
from kivy.metrics import dp
from plotpopup import PlotPopup
from singletransect import SingleTransect
import functions as func


class MultiTransect(ui.widget.Widget):
    # Code for Multiple Transect tool, as well as base code for managing multiple single transects
    def __init__(self, home, **kwargs):
        super(MultiTransect, self).__init__(**kwargs)
        self.lines = []
        self.clicks = 0
        self.p_btn = Button()
        self.mpoints = 0
        self.home = home

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
            data["Cut " + str(count)] = i.ip_get_points()
            count += 1

        # Uses popup code from single_transect
        PlotPopup(data, self.home)

        # Clean up

    def on_touch_down(self, touch):
        # Transect creation and display code
        # Determines what to do based on which of 3 click stages the user is in
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

            # Single transect manages the line and dots graphics
            self.lines[-1].on_touch_down(touch)
            if self.clicks == 1:
                # If clicked same point as before, do nothing
                if [touch.x, touch.y] == self.lines[-1].line.points:
                    return
                # Finishes a transect, displays download button

                self.p_btn = func.RoundedButton(text="Plot", size_hint=(1, 0.1))
                self.home.ids.sidebar.add_widget(self.p_btn, 1)
                self.p_btn.bind(on_press=lambda x: self.popup())
            self.clicks += 1
