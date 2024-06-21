"""
Widget for Transect tool

Manages having multiple SingleTransects on screen at once.
"""
import kivy.uix as ui
from cutview.plotpopup import PlotPopup
from cutview.singletransect import SingleTransect
import cutview.functions as func
from kivy.core.window import Window


class MultiTransect(ui.widget.Widget):
    """
    Creates, stores, and manages multiple SingleTransects

    Created when Transect button is selected. From there on this object manages the creation, modification,
    and data packaging of transects made by user. Also used by marker to manage SingleTransects made
    orthogonally to user marked line.

    Attributes:
        lines: List of SingleTransects made.
        clicks: Int, Number of clicks made by user. Cycles between 0 and 2 depending on current stage of
            transect drawing.
        home: Reference to root HomeScreen instance
        p_btn: RoundedButton, Plot button which opens PlotPopup
        dragging: Boolean, Whether in dragging mode

        Inherits additional attributes from kivy.uix.widget.Widget (see kivy docs)
    """
    def __init__(self, home, **kwargs):
        """
        Initialize object and create Plot button.

        Args:
            home: Reference to root HomeScreen instance
        """
        super(MultiTransect, self).__init__(**kwargs)
        self.lines = []
        self.clicks = 0
        self.home = home
        self.p_btn = func.RoundedButton(text="Plot", size_hint=(1, 0.1), font_size=self.home.font)
        self.p_btn.bind(on_press=lambda x: self.popup())
        self.dragging = False

    def font_adapt(self, font):
        """
        Updates font size of Plot button.

        Args:
            font: Float, new font size
        """
        self.p_btn.font_size = font

    def del_line(self):
        """
        Delete all clicked points in most recent transect
        """
        for i in range(self.clicks):
            self.del_point()

    def del_point(self):
        """
        Delete most recent clicked point
        """
        if len(self.lines) == 0:  # If no transects, do nothing
            return
        elif self.children[0].circles == 1:
            # Case where point is beginning of a transect
            Window.unbind(mouse_pos=self.children[0].draw_line)
            self.remove_widget(self.children[0])
            self.lines = self.lines[:-1]
            # Add plot button to sidebar if not the last transect
            if len(self.lines) != 0:
                self.home.display.current.insert(0, self.p_btn)
        elif self.children[0].circles == 2:
            # Case where point is end of a transect
            self.children[0].del_point()
            if self.p_btn in self.home.display.current:
                # Remove plot button from sidebar
                self.home.display.current.remove(self.p_btn)
        if self.clicks == 2:
            self.clicks = 0
        self.clicks += 1

    def change_dragging(self, val):
        """
        Update whether in dragging mode

        Args:
            val: Boolean, whether in dragging mode or not
        """
        self.dragging = val

    def popup(self):
        """
        Gathers coordinates from SingleTransects into a dictionary and calls for popup
        """
        data = {}
        count = 1
        for i in self.lines:
            data["Cut " + str(count)] = i.line.points
            count += 1
        # Open plotting popup
        PlotPopup({"Multi": data}, self.home, self.home.display.config)

    def on_touch_down(self, touch):
        """
        Creating transects and managing Plot button based on which of 3 click stages user is in.

        Args:
            touch: MouseMotionEvent, see kivy docs for details
        """
        if not self.dragging:
            if self.home.ids.view.collide_point(*self.home.ids.view.to_widget(*self.to_window(*touch.pos))):
                if self.clicks == 2:
                    # Clean up Plot button from previous cycle and reset
                    self.clicks = 0
                    self.home.ids.sidebar.remove_widget(self.p_btn)
                if self.clicks == 0:
                    # Begins a new transect
                    x = SingleTransect(home=self.home)

                    self.add_widget(x)
                    self.lines.append(x)
                # If clicked same point as before, do nothing
                if [touch.x, touch.y] == self.lines[-1].line.points:
                    return
                # SingleTransect manages the line and dots graphics
                self.lines[-1].on_touch_down(touch)
                if self.clicks == 1:
                    # Finishes a transect, displays download button
                    if self.p_btn not in self.home.ids.sidebar.children:
                        self.home.ids.sidebar.add_widget(self.p_btn, 1)
                self.clicks += 1
