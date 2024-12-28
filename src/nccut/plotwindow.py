"""
Functionality for the interactive plot and the adjustable axes in the plotting popup menu when all z levels are plotted
as an image.
"""

from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.metrics import dp
from kivy.uix.label import Label
from kivy.graphics import Line, Color
from kivy.graphics.context_instructions import PushMatrix, Rotate, PopMatrix
from kivy.lang import Builder
from nccut.interactiveplot import InteractivePlot
import nccut.functions as func
import numpy as np
import pathlib

KV_FILE_PATH = pathlib.Path(__file__).parent.resolve() / "plotwindow.kv"
Builder.load_file(str(KV_FILE_PATH))


class YAxis(FloatLayout):
    """
    Manages the tick labels and locations for the y axis of the interactive plot.

    Attributes:
        font (float): Font size for the y axis label and tick labels.
        z_var (str): Name of the z coordinate to use as y axis label.
        z_coords: Z coordinate array. If the datasets selected z dimension is numeric then those coordinate values are
            used, otherwise the index positions of the coordinates are used.
        window: RelativeLayout object which holds the plotting menu and has been reshaped to the plot at it's
            maximum possible size.
        size_hint: Relative size of the object, set to none so the size can be set directly.
        size: Size of the object.
        pos: Position of the object.
        y_label: Label object for the y axis label (z coordinate name).
        y_tick_labels (list): List of y tick labels
    """
    def __init__(self, config, window_box, main, font, **kwargs):
        """
        Initializes y axis and creates y axis label.

        Args:
            config (dict): Dictionary of configuration information about the laoded NetCDF file (see
                :meth:`nccut.netcdfconfig.NetCDFConfig.check_inputs` for structure of dictionary).
            window_box: RelativeLayout object which holds the plotting menu and has been reshaped to the plot at it's
                maximum possible size.
            main: RelativeLayout object where all plotting widgets are placed except the color bar.
            font (float): Font size for the y axis label and tick labels.
        """
        super(YAxis, self).__init__(**kwargs)
        self.font = font
        z_attrs = config["data"][config["z"]].attrs
        if "long_name" in list(z_attrs.keys()):
            self.y_label_text = z_attrs["long_name"].title()
        else:
            self.y_label_text = config["z"].title()
        if "units" in list(z_attrs.keys()):
            self.y_label_text = self.y_label_text + " (" + z_attrs["units"] + ")"
        # Determine whether z coordinate values can be used for the y axis
        try:
            self.z_coords = config["data"][config["z"]].data.astype(float)
            if self.z_coords[1] < self.z_coords[0]:
                self.z_coords = np.flip(self.z_coords)
        except ValueError:
            self.z_coords = np.arange(0, len(config["data"][config["z"]].data))
        # Assumption made in order to be able to plot an image despite their being same number of coords as data points
        self.z_coords = np.append(self.z_coords, self.z_coords[-1] + ((self.z_coords[-1] - self.z_coords[-2]) / 2))
        self.window = window_box
        self.size_hint = (None, None)
        self.size = (0.1 * main.width, self.window.height)
        self.pos = (self.window.x - self.width, self.window.y)
        self.y_label = Label(text=self.y_label_text, color=[0, 0, 0, 1], halign="center", valign="center",
                             size_hint=(None, None), size=(self.font, self.height),
                             pos=(self.right - self.font * 4, self.y), font_size=self.font)
        # Rotate Y label
        with self.y_label.canvas.before:
            PushMatrix()
            Rotate(angle=90, origin=self.y_label.center)
        with self.y_label.canvas.after:
            PopMatrix()
        self.y_tick_labels = []
        self.add_widget(self.y_label)
        # Initialize axes
        self.on_plot_change((0, 0), self.window.size)

    def on_plot_change(self, n_pos, n_size):
        """
        Determines the optimal positioning and distribution of y ticks and labels for the current plot size and
        position. Y tick label values come from the selected z dimension.

        Args:
            n_pos (tuple): The current position of the plot (x, y) relative to the viewing window.
            n_size (tuple): The current size of the plot (w, h).
        """
        self.canvas.remove_group("y_ticks")
        # Determine goal tick density (not necessarily the actual density)
        d = self.height / 50
        if d < 2:
            d = 2
        elif d > 9:
            d = 9
        # Identify ideal y tick labels and whether to use scientific notation
        # Assume origin for coordinate data is top left as with numpy array indexing
        cpp = (self.z_coords[-1] - self.z_coords[0]) / n_size[1]
        y_max = (self.height - n_pos[1]) * cpp
        y_min = (-n_pos[1]) * cpp
        lab_min = y_min + np.min(self.z_coords)
        lab_max = y_max + np.min(self.z_coords)
        if y_min >= y_max:
            selected_labels = [y_min]
        else:
            selected_labels = func.label_placer(lab_min, lab_max, d)
            selected_labels = selected_labels[np.where((selected_labels >= lab_min) & (selected_labels <= lab_max))]
            if len(selected_labels) < 2:
                selected_labels = [lab_min, lab_max]
        rep = "{:.2e}".format(selected_labels[0])
        exp_str = rep[rep.find("e"):]
        exp = int(exp_str[1:])
        if abs(exp) > 2:
            formatted_labels = [round(elem / 10 ** exp, 2) for elem in selected_labels]
            exp_str = " (" + exp_str + ")"
        else:
            formatted_labels = [round(elem, 2) for elem in selected_labels]
            exp_str = ""
        formatted_labels = [int(lab) if lab.is_integer() else lab for lab in formatted_labels]
        # Calculate y tick positions of the chosen y tick labels
        # Assume origin for coordinate data is top left as with numpy array indexing
        label_ticks = selected_labels - np.min(self.z_coords)
        selected_t_pos = [(s / cpp) + n_pos[1] + self.y for s in label_ticks]
        tick_x = self.right
        # Draw y ticks
        with self.canvas:
            Color(0, 0, 0)
            for p in selected_t_pos:
                Line(points=[tick_x - dp(6), p, tick_x - dp(1), p], width=dp(1), cap="none", group="y_ticks")

        # Add or remove labels until have required amount
        while len(self.y_tick_labels) < len(formatted_labels):
            lab = Label(text="", color=[0, 0, 0, 1], halign="left", size_hint=(None, None), font_size=self.font)
            lab.bind(texture_size=lab.setter("size"))
            self.y_tick_labels.append(lab)
            self.add_widget(lab)
        while len(self.y_tick_labels) > len(formatted_labels):
            self.remove_widget(self.y_tick_labels.pop(0))
        # Place y tick labels
        for i, y in enumerate(formatted_labels):
            lab = self.y_tick_labels[i]
            lab.text = str(y)
            lab.pos = (tick_x - self.font * 2.5, float(selected_t_pos[i]) - self.font / 2)

        # Update y label
        self.y_label.text = self.y_label_text + exp_str


class XAxis(FloatLayout):
    """
    Manages the tick labels and locations for the x axis of the interactive plot.

    Attributes:
        font (float): Font size for the x axis label and tick labels.
        window: RelativeLayout object which holds the plotting menu and has been reshaped to the plot at it's
            maximum possible size.
        size_hint: Relative size of the object, set to none so the size can be set directly.
        size: Size of the object.
        pos: Position of the object.
        x_label: Label object for the x axis label (Along Transect Point).
        transect_points (int): Number of pixels in transect
        x_axis_labels (list): List of x tick labels

    """
    def __init__(self, window_box, main, font, transect_points, **kwargs):
        """
        Initializes x axis and creates x axis label

        Args:
            window_box: RelativeLayout object which holds the plotting menu and has been reshaped to the plot at it's
                maximum possible size.
            main: RelativeLayout object where all plotting widgets are placed except the color bar.
            font (float): Font size for the x axis label and tick labels.
            transect_points (int): Number of pixels in transect
        """
        super(XAxis, self).__init__(**kwargs)
        self.font = font
        self.window = window_box
        self.size_hint = (None, None)
        self.size = (self.window.width, 0.12 * main.height)
        self.pos = (self.window.x, self.window.y - self.height)
        self.x_label = Label(text="Along Transect Point", color=[0, 0, 0, 1], halign="center", size_hint=(None, None),
                             size=self.size, pos=self.pos, font_size=font, text_size=(None, self.height))
        self.add_widget(self.x_label)
        self.transect_points = transect_points
        self.x_tick_labels = []
        self.on_plot_change((0, 0), self.window.size)

    def on_plot_change(self, n_pos, n_size):
        """
        Determines the optimal positioning and distribution of x ticks and labels for the current plot size and
        position. X tick label values are between zero and the length of the transect.

        Args:
            n_pos (tuple): The current position of the plot (x, y) relative to the viewing window.
            n_size (tuple): The current size of the plot (w, h).
        """
        self.canvas.remove_group("x_ticks")
        # Determine goal tick density (not necessarily the actual density)
        d = self.width / 70
        if d < 2:
            d = 2
        elif d > 9:
            d = 9
        # Identify ideal x tick labels
        cpp = self.transect_points / n_size[0]
        x_min = -n_pos[0] * cpp
        x_max = (self.width - n_pos[0]) * cpp
        if x_min >= x_max:
            selected_labels = [x_min]
        else:
            selected_labels = func.label_placer(x_min, x_max, d)
            selected_labels = selected_labels[np.where((selected_labels >= x_min) & (selected_labels <= x_max))]
            if len(selected_labels) < 2:
                selected_labels = [x_min, x_max]
        # Calculate x tick positions of the chosen x tick labels
        selected_t_pos = [x / cpp + self.x + n_pos[0] for x in selected_labels]
        tick_top = self.y + self.height
        # Draw x ticks
        with self.canvas:
            Color(0, 0, 0)
            for p in selected_t_pos:
                Line(points=[p, tick_top, p, tick_top - dp(5)], width=dp(1), cap="none", group="x_ticks")

        # Add or remove labels until have required amount
        while len(self.x_tick_labels) < len(selected_labels):
            lab = Label(text="", color=[0, 0, 0, 1], halign="left", size_hint=(None, None), font_size=self.font)
            lab.bind(texture_size=lab.setter("size"))
            self.x_tick_labels.append(lab)
            self.add_widget(lab)
        while len(self.x_tick_labels) > len(selected_labels):
            self.remove_widget(self.x_tick_labels.pop(0))

        # Place x tick labels
        for i, x in enumerate(selected_labels):
            lab = self.x_tick_labels[i]
            lab.text = str(np.round(x, 3))
            lab.pos = (float(selected_t_pos[i]) - self.font / 2, tick_top - self.font * 1.6)


class PlotWindow(RelativeLayout):
    """
    Manages the functionality of the interactive plot and the dynamic axes as well as creating the colorbar. Static UI
        elements are defined in plotwindow.kv

    Args:
        config (dict): Dictionary of configuration information about the laoded NetCDF file (see
            :meth:`nccut.netcdfconfig.NetCDFConfig.check_inputs` for structure of dictionary).
        z_data (arr): 2D Numpy Array of transect data for all z values to be plotted.
        resized (int): How many times the window has been resized. Used to ensure children widget sizes are determined
            only after the plotting widget has reached it's full size.
        plot: Reference to current :class: `nccut.interactiveplot.InteractivePlot` object
        x_axis: Reference to current :class: `nccut.plotwindow.XAxis` object
        y_axis: Reference to current :class: `nccut.plotwindow.YAxis` object
        font (float): Font size to use for all text elements in the plotting window
        colormap(str): Matplotlib colormap to use for plot
    """
    def __init__(self, config, z_data, colormap, **kwargs):
        """
        Initialized object according to all z data to be plotted

        Args:
            config (dict): Dictionary of configuration information about the laoded NetCDF file (see
                :meth:`nccut.netcdfconfig.NetCDFConfig.check_inputs` for structure of dictionary).
            z_data (arr): 2D Numpy Array of transect data for all z values to be plotted.
            colormap (str): Matplotlib colormap to use for plot
        """
        super(PlotWindow, self).__init__(**kwargs)
        self.config = config
        self.z_data = z_data
        self.resized = 0
        self.plot = None
        self.x_axis = None
        self.y_axis = None
        self.font = None
        self.max_c_bar_font = dp(45)
        self.colormap = colormap

    def load(self, *args):
        """
        Loads all plotting widgets once this widget has reached it's final size so children are sized correctly.

        Creates InteractivePlot which determines it's own maximum size and centered position, and then fits the
        StencilView window to the plot along with a black border. Then the axes, title widgets, and color bar are
        positioned and sized according to the StencilView window.
        """
        if not self.resized == 0:
            self.canvas.remove_group(str(self.resized - 1))
            self.remove_widget(self.x_axis)
            self.remove_widget(self.y_axis)
            self.ids.window.remove_widget(self.plot)
            self.ids.color_bar_box.remove_widget(self.ids.color_bar_box.children[0])

        self.plot = InteractivePlot(self.z_data, self.config["data"][self.config["z"]], [0.7, 0.75], self)
        # Size and position of StencilView are set to that of the plot at it's minimum size that fills the widget
        self.ids.window_box.size = self.plot.bbox[1]
        self.ids.window.add_widget(self.plot)
        self.ids.window_box.pos = (0.45 * self.width - 0.5 * self.plot.bbox[1][0],
                                   0.525 * self.height - 0.5 * self.plot.bbox[1][1])
        wb = self.ids.window_box
        # Draw box around plot
        with self.canvas:
            Color(0, 0, 0)
            Line(points=[wb.x, wb.y, wb.right, wb.y], width=dp(1), cap="square", group=str(self.resized))
            Line(points=[wb.x, wb.top, wb.right, wb.top], width=dp(1), cap="square", group=str(self.resized))
            Line(points=[wb.x, wb.y, wb.x, wb.top], width=dp(1), cap="square", group=str(self.resized))
            Line(points=[wb.right, wb.y, wb.right, wb.top], width=dp(1), cap="square", group=str(self.resized))
        # Choose font
        self.font = min(0.03 * self.height, 0.02 * self.width)
        # Place plot title

        var_attrs = self.config["data"][self.config["var"]].attrs
        if "long_name" in list(var_attrs.keys()):
            title = var_attrs["long_name"].title()
        else:
            title = self.config["var"].title()
        if "units" in list(var_attrs.keys()):
            title = title + " (" + var_attrs["units"] + ")"

        self.ids.title.text = title
        self.ids.title.font_size = self.font
        self.ids.title.size = (0.55 * self.width, 0.1 * self.height)
        self.ids.title.pos = (wb.center_x - self.ids.title.width / 2, wb.pos[1] + wb.height)
        # Create axes (they place themselves)
        self.x_axis = XAxis(wb, self, self.font, self.z_data.shape[1])
        self.y_axis = YAxis(self.config, wb, self, self.font)
        self.add_widget(self.x_axis)
        self.add_widget(self.y_axis)
        # Create and add colorbar
        if min(0.02 * self.height, 0.02 * self.width) == 0.02 * self.width:
            c_bar_font = self.font * 2
        else:
            c_bar_font = self.font * 4
        if c_bar_font > self.max_c_bar_font:
            c_bar_font = self.max_c_bar_font
        self.ids.color_bar_box.add_widget(func.get_color_bar(self.colormap, self.z_data, (1, 1, 1), "black",
                                                             c_bar_font))

        self.resized += 1

    def update_axes(self):
        """
        Signals axes to adjust to new plot. Triggered any time the interactive plot changes size or position.
        """
        self.x_axis.on_plot_change(*self.plot.bbox)
        self.y_axis.on_plot_change(*self.plot.bbox)
