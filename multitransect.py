"""
Class for multiple transect tool that manages any case where multiple single transects are needed.
"""
import kivy.uix as ui
from kivy.uix.button import Button
from kivy.metrics import dp
from kivy.graphics import Color
from singletransect import SingleTransect
import functions as func


class MultiTransect(ui.widget.Widget):
    # Code for Multiple Transect tool, as well as base code for managing multiple single transects
    def __init__(self, home, **kwargs):
        super(MultiTransect, self).__init__(**kwargs)
        self.lines = []
        self.clicks = 0
        self.dbtn = Button()
        self.remove = True
        self.test = False # Is this in use?
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
        self.lines[0].plot_popup(data)

        # Clean up
        self.home.ids.view.parent.remove_widget(self.dbtn)
        if self.remove:
            self.parent.remove_widget(self.parent.children[0])

    def on_touch_down(self, touch):
        # Transect creation and display code
        # Determines what to do based on which of 3 click stages the user is in

        if self.clicks == 2:
            # Clean up download button from previous cycle
            self.clicks = 0
            if not self.test:
                self.home.ids.view.parent.remove_widget(self.dbtn)

        if self.clicks == 0:
            # Begins a new transect
            x = SingleTransect(buttons=False, home=self.home)

            self.add_widget(x)
            self.lines.append(x)

        # Single transect manages the line and dots graphics
        self.lines[-1].on_touch_down(touch)
        if self.clicks == 1:
            # If clicked same point as before, do nothing
            if [touch.x, touch.y] == self.lines[-1].line.points:
                return
            # Finishes a transect, displays download button
            if not self.test:
                self.dbtn = func.RoundedButton(text="Download", pos_hint={'x': .85, 'y': 0.02}, size=(dp(100), dp(30)),
                                   size_hint_x=None, size_hint_y=None)
                self.home.ids.view.parent.add_widget(self.dbtn)
                self.dbtn.bind(on_press=lambda x: self.popup())
        self.clicks += 1
