# SPDX-FileCopyrightText: 2024 University of Washington
#
# SPDX-License-Identifier: BSD-3-Clause

"""
Miscellaneous helper functions to support other widgets.

Provides reference to custom UI elements defined in nccut.kv file so they can be used in python scripts.
Contains error banner functionality, file management function, and transect taking function.

"""

import kivy
from kivy.graphics import Color, Rectangle, Line
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.metrics import dp
from kivy.core.image import Image as CoreImage
import kivy.uix as ui
from functools import partial
from scipy.interpolate import RegularGridInterpolator, CubicSpline
import numpy as np
from PIL import Image as im
import math
import io
import warnings
import itertools
import matplotlib
from pathlib import Path
import tomli
import os
matplotlib.use('Agg')
import matplotlib.pyplot as plt


class Click:
    """
    Object that mimics a user click.

    Attributes:
        x (float): X coordinate of click point
        y (float): Y coordinate of click point
        pos (tuple): 2 element tuple: (X coord, Y coord)
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.pos = (x, y)
        self.is_double_tap = False
        self.button = "left"


class RoundedButton(Button):
    """
    Code for this is in nccut.kv. Referenced here so it can be used in scripts.
    """
    pass


class BackgroundLabel(Label):
    """
    Code for this is in nccut.kv. Referenced here so it can be used in scripts.
    """
    def __init__(self, background_color=[0, 0, 0, 1], **kwargs):
        super(BackgroundLabel, self).__init__(**kwargs)
        self.background_color = background_color


class SidebarHeaderLabel(BackgroundLabel):
    def __init__(self, text="", **kwargs):
        super().__init__(**kwargs)
        self.text_size = self.size  # Initial constraint
        self.bind(size=self.update_text_size)
        self.text = text
        self.background_color = [0.2, 0.2, 0.2, 1]
        self.size_hint_y = None
        self.height = dp(40)
        self.halign = "center"
        self.valign = "center"
        with self.canvas.before:
            self.color_instruction = Color(1, 1, 1, 1)
            self.line = Line(width=dp(1), cap="square", points=[self.x, self.y, self.x + self.width, self.y])
        self.bind(pos=self.update_line, size=self.update_line)  # Keep the line in place

    def update_text_size(self, *args):
        """Ensure text_size always matches the label's size."""
        self.text_size = self.size

    def update_line(self, *args):
        """Update the line position when the label moves or resizes."""
        self.line.points = [self.x, self.y, self.x + self.width, self.y]


class AlertPopup(Popup):
    """
    Displays a popup with the given message as well as a back button. Adapts to the height of the text.

    UI Code for this is in nccut.kv. This code outlines the functionality for the popup.
    """

    def update_height(self, height):
        """
        Updates popup height to match text height

        Args:
            height: Text height
        """
        new_height = max(height, dp(40))
        self.height = new_height + dp(60)

    def quit(self):
        """
        Closes popup
        """
        self.dismiss()

    def set_message(self, message):
        """
        Sets popup message

        Args:
            message (str): Text to display
        """
        self.ids.message.text = message


def validate_config(config):
    """
    Given a dictionary parsed from a configuration file, ensures that no invalid elements or values are present.

    Args:
        config: Dictionary parsed from a configuration file of configuration sections, keys, and values

    Returns:
        True if configuration is valid, False if any invalid elements or values we're found
    """
    keys = list(config.keys())

    xyz = [list(i) for i in list(itertools.permutations(["x", "y", "z"], 3))]
    allowed_options = {"graphics_defaults": {"contrast": np.arange(-20, 21).astype(int),
                                             "line_color": ["Blue", "Orange", "Green"],
                                             "colormap": plt.colormaps()[:87],
                                             "circle_size": np.arange(2, 71).astype(int),
                                             "font_size": np.arange(8, 21)},
                       "tool_defaults": {"orthogonal_width": np.arange(0, 401).astype(int)},
                       "netcdf": {"dimension_order": xyz},
                       "metadata": {}}

    if not all([key in list(allowed_options.keys()) for key in keys]):
        return False
    for key in keys:
        sub_keys = list(config[key].keys())
        if key == "metadata":
            vals = list(config[key].values())
            if len(vals) > 0 and not all(isinstance(item, str) for item in vals):
                return False
        else:
            if not all([k in list(allowed_options[key].keys()) for k in sub_keys]):
                return False
            for subkey in list(config[key].keys()):
                if not config[key][subkey] in allowed_options[key][subkey]:
                    return False
    return True


def convert_found_coords(found, config):
    """
    If coordinates from loaded project file came from the currently loaded NetCDF file convert the coordinates to
    pixel coordinates for plotting the chains on the viewer.

    Args:
        config:
        found: The found chains from the project file that have already been verified to have come from the current
            NetCDF file. A list containing a list for each chain which contains three lists: [X Coord List,
            Y Coord List, Width List]

    Returns:
        The original found list except the Click points have been converted to pixel coordinates
    """
    for chain in found:
        for i, c in enumerate(["x", "y"]):
            coords = config["netcdf"]["data"].coords[config["netcdf"][c]].data.astype(float)
            c_spline = CubicSpline(coords, range(len(coords)))
            chain[i] = c_spline(chain[i]).tolist()
    return found


def find_config(config_file):
    """
    Looks for nccut_config.toml file. If found, validates and applied configuration changes.

    Looks for an environment variable 'NCCUT_CONFIG' holding the config file. If not found, looks in the current
    working directory and then in either '%APPDATA%\nccut\nccut_config.toml' on Windows or
    '~/.config/your_app/config.toml' on Linux and macOS

    Args:
        config_file (str): Path to configuration file given by user on command line start. Empty string if none was
            given.

    Returns:
        If valid configuration file, returns dictionary of config values. If none was found or invalid, returns empty
        dictionary.
    """
    config_path = os.getenv('NCCUT_CONFIG')
    if config_file:
        # Check if config file passed in as a command line argument
        config_path = config_file
    elif config_path:
        # Check if an environment variable is set for the config file
        config_path = Path(config_path)
    else:
        # Look for file in working directory
        config_path = Path.cwd() / "nccut_config.toml"
        if not config_path.is_file():
            # Look for file in default location
            if os.name == 'nt':  # Windows
                config_path = Path(os.getenv('APPDATA')) / 'nccut' / 'nccut_config.toml'
            else:  # Unix-based systems (Linux/macOS)
                config_path = Path.home() / ".config" / "nccut" / "nccut_config.toml"
    try:
        with open(config_path, 'rb') as config_file:
            config = tomli.load(config_file)
            if validate_config(config):
                print(f"Valid configuration file found at {config_path}")
                return config
            else:
                print(f"Invalid configuration file ignored. File found at {config_path}")
                return {}
    except FileNotFoundError:
        return {}


def chain_find(data, res, need, c_type):
    """
    Recursively examines dictionary and determines if dictionary is valid project file containing the needed fields.

    Args:
        data (dict): Dictionary to examine
        res (list): Empty list to fill with chain click coordinates and orthogonal transect widths
        need (list): List of required fields to qualify as an orthogonal chain:
            ["Click <cord>", "Click <cord>", "Width"]
        c_type: Type of chain to look for

    Returns:
        Nested List. A list containing a list for each orthogonal chain which each contains three lists:
        click X coords, click y coords, and the orthogonal transect width for each click point in the chain.
        If no qualifying data was found returns empty list. If duplicate data is found (ex: multiple
        variables in a file) only returns one instance of orthogonal chain data.
    """
    for key in list(data.keys()):
        if key[0:len(c_type)] == c_type:
            if correct_test(data[key], need):  # Orthogonal chain dict has necessary fields
                if len(res) == 0:  # If res empty, always add orthogonal chain data
                    new_items = []
                    for i in range(len(need)):
                        new_items.append(data[key][need[i]])
                    res.append(new_items)
                else:  # If res not empty, ensure found orthogonal chain data isn't already in res
                    new = True
                    for item in res:
                        l1 = data[key][need[0]]
                        l2 = item[0]
                        if len(l1) == len(l2) and len(l1) == sum([1 for i, j in zip(l1, l2) if i == j]):
                            new = False
                    if new:
                        new_items = []
                        for i in range(len(need)):
                            new_items.append(data[key][need[i]])
                        res.append(new_items)
        else:
            if type(data[key]) is dict:  # Can still go further in nested dictionary tree
                chain_find(data[key], res, need, c_type)
            else:
                return res
    return res


def correct_test(data, need):
    """
    Check if dictionary has necessary fields to be an orthogonal chain

    Args:
        data (dict): Dictionary to be tested.
        need (list): List of required fields to qualify as an orthogonal chain:
            ["Click <cord>", "Click <cord>", "Width"]

    Returns:
        Boolean, whether dictionary has necessary keys with a list has the value
    """
    keys = list(data.keys())
    if len(keys) == 0:
        return False
    else:
        for item in need:
            if item not in keys or not isinstance(data[item], list):
                return False
    return True


def contrast_function(value):
    """
    Function to transform a setting value to the actual contrast value to apply with PIL.

    Transforms domain [-20, 20] to [0, 2]

    Args:
        value (int): The user selected contrast setting value

    Returns:
        Float, contrast value to actually apply to the image.
    """
    v = float(value) / 20
    if v < 0:
        contrast = 1 + v
    else:
        contrast = 1 + v * 2
    return contrast


def text_wrap(*args):
    """
    Updates a widgets text box so that it is always within the bounds of the widget.

    Args:
        args: List where first item is a Button or Label and the second item is a tuple of that widgets current size.
    """
    args[0].text_size = (args[1][0] - dp(12), args[1][1] - dp(12))


def remove_alert(alert, home, *largs):
    """
    Remove alert banner.

    Args:
        alert: Alert kivy.uix.label.Label reference.
        home: Active :class:`nccut.homescreen.HomeScreen` instance.
        *largs: Unused args from kivy Clock class.
    """
    home.remove_widget(alert)


def alert(text, home):
    """
    Creates alert banner.

    Creates alert banner with given text and adds it to top left corner of the home screen.
    Schedules it to be removed after 2 seconds.

    Args:
        text (str): Alert banner message
        home: Active :class:`nccut.homescreen.HomeScreen` reference
    """

    screen = kivy.core.window.Window.size
    with home.canvas:
        Color(0.2, 0.2, 0.2)
        box = Rectangle(pos=(dp(10), kivy.core.window.Window.size[1] - dp(60)), size=(dp(300), dp(50)))
    aler = Label(text=text, size=home.size, pos=(-(screen[0] / 2) + dp(160), screen[1] / 2 - dp(35)))
    home.add_widget(aler)
    kivy.clock.Clock.schedule_once(partial(remove_alert, aler, home), 2)
    kivy.clock.Clock.schedule_once(partial(home.canvas_remove, box), 2)


def alert_popup(text):
    """
    Creates popup with an alert with given text.

    Args:
        text (str): Alert message
    """
    popup = AlertPopup()
    popup.set_message(text)
    popup.open()


def simplicity(q, q_arr, j, l_min, l_max, l_step):
    """
    Calculates simplicity score

    Args:
        q: Current step size
        q_arr: Preference-ordered list of 'nice numbers' to choose from
        j: Amount of elements to skip in current step size sequence
        l_min: Start of labeling sequence
        l_max: End of labeling sequence
        l_step: Labeling sequence step size

    Returns:
        Simplicity score that prefers step sizes that appear earlier in Q, penalizes large j's, and rewards label
        sequences that include 0.

    References:
        Talbot, Lin and Hanrahan, 'An Extension of Wilkinson’s Algorithm for Positioning Tick Labels on Axes',
            IEEE Transactions on Visualization and Computer Graphics (2010)
    """
    eps = 1 * 10**-10
    n = len(q_arr)
    i = np.argwhere(q_arr == q)[0][0] + 1
    if l_min - l_step * np.floor(l_min / l_step) < eps and l_min <= 0 and l_max >= 0:
        v = 1
    else:
        v = 0
    return 1 - (i - 1) / (n - 1) - j + v


def simplicity_max(q, q_arr, j):
    """
    Calculates maximum possible simplicity score

    Args:
        q: Current step size
        q_arr: Preference-ordered list of 'nice numbers' to choose from
        j: Amount of elements to skip in current step size sequence

    Returns:
        Maximum possible simplicity score for current step size and skip amount

    References:
        Talbot, Lin and Hanrahan, 'An Extension of Wilkinson’s Algorithm for Positioning Tick Labels on Axes',
            IEEE Transactions on Visualization and Computer Graphics (2010)
    """
    n = len(q_arr)
    i = np.argwhere(q_arr == q)[0][0] + 1
    v = 1
    return 1 - (i - 1) / (n - 1) - j + v


def coverage(d_min, d_max, l_min, l_max):
    """
    Calculates coverage score

    Args:
        d_min: Start of data range
        d_max: End of data range
        l_min: Start of proposed label sequence
        l_max: End of proposed label sequence

    Returns:
        Coverage score that encourages balanced labels with roughly equal amounts of whitespace on both ends, with
        rarely more than 20% whitespace

    References:
        Talbot, Lin and Hanrahan, 'An Extension of Wilkinson’s Algorithm for Positioning Tick Labels on Axes',
            IEEE Transactions on Visualization and Computer Graphics (2010)
    """
    return 1 - 0.5 * ((d_max - l_max) ** 2 + (d_min - l_min) ** 2) / ((0.1 * (d_max - d_min)) ** 2)


def coverage_max(d_min, d_max, span):
    """
    Calculates maximum possible coverage score

    Args:
        d_min: Start of data range
        d_max: End of data range
        span: Length of label range

    Returns:
         Maximum possible coverage score for the data range and current label range

    References:
        Talbot, Lin and Hanrahan, 'An Extension of Wilkinson’s Algorithm for Positioning Tick Labels on Axes',
            IEEE Transactions on Visualization and Computer Graphics (2010)
    """
    d_range = d_max - d_min
    if span > d_range:
        half = (span - d_range) / 2
        return 1 - 0.5 * (half ** 2 + half ** 2) / ((0.1 * d_range) ** 2)
    else:
        return 1


def density(k, m, d_min, d_max, l_min, l_max):
    """
    Calculates density score

    Args:
        k: Number of labels in label sequence
        m: User provided target label density
        d_min: Start of data range
        d_max: End of data range
        l_min: Start of proposed label sequence
        l_max: End of proposed label sequence

    Returns:
        Density score based on how close the label density is to the user provided target density

    References:
        Talbot, Lin and Hanrahan, 'An Extension of Wilkinson’s Algorithm for Positioning Tick Labels on Axes',
            IEEE Transactions on Visualization and Computer Graphics (2010)
    """
    r = (k - 1) / (l_max - l_min)
    rt = (m - 1) / (max(l_max, d_max) - min(d_min, l_min))
    return 2 - max(r / rt, rt / r)


def density_max(k, m):
    """
    Calculates maximum possible density score.

    Args:
        k: Number of labels in label sequence
        m: User provided target label density

    Returns:
        Maximum possible density score given the current number of labels in the sequence and the provided target
        density

    References:
        Talbot, Lin and Hanrahan, 'An Extension of Wilkinson’s Algorithm for Positioning Tick Labels on Axes',
            IEEE Transactions on Visualization and Computer Graphics (2010)
    """
    if k >= m:
        return 2 - (k - 1) / (m - 1)
    else:
        return 1


def label_placer(d_min, d_max, m, q_arr=np.array([1, 5, 2, 4, 3]), w=np.array([0.2, 0.25, 0.5, 0.05])):
    """
    Algorithm for determining ideal axis labels in a way that optimizes a simplicity, legibility, coverage, and density
    score.

    Args:
        d_min: Start of data range
        d_max: End of data range
        m: User provided target label density
        q_arr: Preference-ordered list of 'nice numbers' to choose from
        w: Four element array of weights for the four axis qualities used to calculate final score

    Returns:
        Array of selected axis labels. This implementation of Talbot (et al.)'s algorithm omits the legibility score.

    References:
        Talbot, Lin and Hanrahan, 'An Extension of Wilkinson’s Algorithm for Positioning Tick Labels on Axes',
            IEEE Transactions on Visualization and Computer Graphics (2010)
    """

    best = {"score": -2}
    j = 1
    while j < np.inf:
        for q in q_arr:
            sm = simplicity_max(q, q_arr, j)
            if (w[0] * sm + w[1] + w[2] + w[3]) < best["score"]:
                j = np.inf
                break
            k = 2
            while k < np.inf:  # loop over tick counts
                dm = density_max(k, m)
                if (w[0] * sm + w[1] + w[2] * dm + w[3]) < best["score"]:
                    break
                delta = (d_max - d_min) / (k + 1) / j / q
                z = np.ceil(np.log10(delta))
                while z < np.inf:
                    step = j * q * 10 ** z
                    cm = coverage_max(d_min, d_max, step * (k - 1))
                    if (w[0] * sm + w[1] * cm + w[2] * dm + w[3]) < best["score"]:
                        break
                    min_start = int(np.floor(d_max / step) * j - (k - 1) * j)
                    max_start = int(np.ceil(d_min / step) * j)
                    if min_start > max_start:
                        z = z + 1
                        next
                    for start in range(min_start, max_start):
                        lmin = start * (step / j)
                        lmax = lmin + step * (k - 1)
                        lstep = step
                        c = coverage(d_min, d_max, lmin, lmax)
                        s = simplicity(q, q_arr, j, lmin, lmax, lstep)
                        g = density(k, m, d_min, d_max, lmin, lmax)
                        legibility = 1

                        score = w[0] * c + w[1] * s + w[2] * g + w[3] * legibility

                        if score > best["score"]:
                            best = {"lmin": lmin, "lmax": lmax, "lstep": lstep, "score": score}
                    z = z + 1
                k = k + 1
        j = j + 1
    return np.arange(best["lmin"], best["lmax"] + best["lstep"], best["lstep"])


def get_color_bar(colormap, data, face_color, text_color, font):
    """
    Create color bar image according to colormap and dataset

    Args:
        colormap: cv2 colormap
        data: 2D indexable array of numerical data to apply the to
        face_color: Color (R, G, B) to use as the background color for the image
        text_color (str): Color to use as text color
        font (float): Font to use for tick labels

    Returns:
        kivy.uix.image.Image object containing image of colorbar
    """
    c_arr = (np.arange(0, 256) * np.ones((10, 256))).astype(np.uint8).T
    c_bar = plt.get_cmap(colormap)(c_arr)
    plt.figure(figsize=(1, 30))
    plt.imshow(c_bar, origin="lower")

    ax = plt.gca()
    ax.get_xaxis().set_visible(False)
    with warnings.catch_warnings(record=True):
        d_min = np.nanmin(data)
        d_max = np.nanmax(data)

    if d_min == d_max:
        s_labels = [d_min]
    elif np.isnan(d_min) or np.isnan(d_max):
        s_labels = []
    else:
        s_labels = label_placer(d_min, d_max, 6)
        s_labels = s_labels[np.where((s_labels >= d_min) & (s_labels <= d_max))]
        if len(s_labels) < 2:
            s_labels = [d_min, d_max]
    if len(s_labels) > 0 and s_labels[0] is not None:
        rep = "{:.2e}".format(s_labels[0])
        exp_str = rep[rep.find("e"):]
        exp = int(exp_str[1:])
        if abs(exp) > 2:
            formatted_labels = [round(elem / 10 ** exp, 2) for elem in s_labels]
            exp_str = " (" + exp_str + ")"
        else:
            formatted_labels = [round(elem, 2) for elem in s_labels]
            exp_str = ""
        ticks = [((c - np.nanmin(data)) / (np.nanmax(data) - np.nanmin(data))) * 256 for c in s_labels]
        ax.set_yticks(ticks=ticks, labels=formatted_labels, fontsize=font)
        ax.yaxis.label.set_color(text_color)
        ax.tick_params(axis='y', colors=text_color)
    else:
        exp_str = "NaN"
    ax.set_title("        " + exp_str, color=text_color, fontsize=font)
    temp = io.BytesIO()
    plt.savefig(temp, facecolor=face_color, bbox_inches='tight', format="png")
    temp.seek(0)
    plt.close()
    plot = ui.image.Image(source="", texture=CoreImage(io.BytesIO(temp.read()), ext="png").texture)
    return plot


def subset_around_transect(config, points):
    """
    Determines and loads a subset of the data that surrounds the transect.

    Args:
        config: config (dict): Information necessary for accessing the loaded data. For images this is the file path and
            for NetCDF files this is a dictionary of configuration values (see
            :meth:`nccut.netcdfconfig.NetCDFConfig.check_inputs` for structure of dictionary)
        points: 4 element 1D array with coordinates of the two transect end points: [X1, Y1, X2, Y2]

    Returns:
        Subset of data, rescaled points [X1, Y1, X2, Y2], list of [X, Y] rescale factors>. If passed data is an
        image doesn't do sub-secting since efficiency is less of an issue.
    """
    if isinstance(config, str):
        # Don't subsect if image file
        img = np.flip(np.asarray(im.open(config)), 0)
        return img, points, [0, 0]
    elif config['z'] == 'N/A':
        # 2D NetCDF data
        ds = config['data'][config['var']].rename({config['y']: 'y', config['x']: 'x'})
    else:
        # 3D NetCDF data
        ds = config['data'][config['var']].rename({config['y']: 'y', config['x']: 'x', config['z']: 'z'})
        ds['z'] = ds['z'].astype(str)
        ds = ds.sel(z=config["z_val"])
    ds["x"] = ds["x"].astype(float)
    ds["y"] = ds["y"].astype(float)

    x_points = np.sort(np.array([points[0], points[2]]))
    y_points = np.sort(np.array([points[1], points[3]]))

    # Get original coordinates in ascending order
    if ds["x"][1] < ds["x"][0]:
        og_x = ds["x"][::-1]
    else:
        og_x = ds["x"]

    if ds["y"][1] < ds["y"][0]:
        og_y = ds["y"][::-1]
    else:
        og_y = ds["y"]

    # Create new, equidistant coordinate arrays
    x_pix = min(abs(og_x.data[:-1] - og_x.data[1:]))
    y_pix = min(abs(og_y.data[:-1] - og_y.data[1:]))

    curr_x = np.arange(og_x.min(), og_x.max() + x_pix, x_pix)
    curr_y = np.arange(og_y.min(), og_y.max() + y_pix, y_pix)

    # Convert pixel coordinates to netcdf_coordinates
    x_vals = x_points * x_pix + curr_x.min()
    y_vals = y_points * y_pix + curr_y.min()

    # Determine original data to grab that surrounds selected points
    sub_x = og_x[np.searchsorted(og_x, x_vals[0]) - 1:np.searchsorted(og_x, x_vals[1]) + 1]
    new_x = np.arange(sub_x[0], sub_x[-1] + x_pix, x_pix)
    sub_y = og_y[np.searchsorted(og_y, y_vals[0]) - 1:np.searchsorted(og_y, y_vals[1]) + 1]
    new_y = np.arange(sub_y[0], sub_y[-1] + y_pix, y_pix)
    # Select subset
    sub_data = ds.sel({"x": sub_x, "y": sub_y})
    sub_data = sub_data.transpose("y", "x")
    # Shift points to subset coordinate system

    coord_scales = [curr_x.min(), curr_y.min(), curr_x.min(), curr_y.min()]
    sub_scales = [new_x.min(), new_y.min(), new_x.min(), new_y.min()]
    pix_scales = [x_pix, y_pix, x_pix, y_pix]

    new_points = (np.array(points) * pix_scales + coord_scales - sub_scales) / pix_scales

    # Interpolate subset of data to equidistant grid
    interpolator = RegularGridInterpolator((sub_y, sub_x), sub_data.data, method="linear",
                                           bounds_error=False, fill_value=None)
    X, Y = np.meshgrid(new_x, new_y)
    interp_data = interpolator((Y, X))
    return interp_data, new_points, [new_x.min() - og_x.data.min(), new_y.min() - og_y.data.min()]


def ip_get_points(line, curr, config):
    """
    Creates a data frame containing x, y, and value of points on transect line

    From end points finds points of line connecting them. Interpolates higher resolution version of
    given data set, and then grabs data values at each line point. If the file is a NetCDF file with valid
    coordinates the x, y coordinates are translated to the selected NetCDF coordinates

    Args:
        line: 4 element 1D array with coordinates of the two transect end points: [X1, Y1, X2, Y2]
        curr: 2D indexable array of data in which the transect was taken.
        config (dict): Information necessary for accessing the file. For images this is the file path and for NetCDF
            files this is a dictionary of configuration values (see
            :meth:`nccut.netcdfconfig.NetCDFConfig.check_inputs` for structure of dictionary)

    Returns:
        Dictionary with three keys:
            'x': 1D array of x-coordinates of transect points. If valid NetCDF is loaded these are interpolated from the
                selected x dimension
            'y': 1D array of y-coordinates of transect points. If valid NetCDF is loaded these are interpolated from the
                selected y dimension
            'Cut': 1D array of data values at each point along line connecting end points. If from an image the data
                value is the mean of the pixel RGB values. If from a NetCDF file the data comes from the loaded Dataset.
    """

    # If angle of line is > 45 degrees will swap x and y to increase accuracy
    xyswap = False
    flipped = False
    img = np.asarray(curr)
    # Always read from left point to right
    if line[0] > line[2]:
        flipped = True
        line = [line[2], line[3], line[0], line[1]]

    # Calculate slope
    if line[2] - line[0] == 0:
        m = (line[3] - line[1]) / .001
    else:
        m = (line[3] - line[1]) / (line[2] - line[0])
    # If slope greater than 45 deg swap x, y
    if abs(math.atan(m)) > (math.pi / 4):
        xyswap = True
        line = [line[1], line[0], line[3], line[2]]
        # Recalculate slope with new order
        if line[2] - line[0] == 0:
            m = (line[3] - line[1]) / .001
        else:
            m = (line[3] - line[1]) / (line[2] - line[0])
        x_lab = "y"
        y_lab = "x"
    else:
        x_lab = "x"
        y_lab = "y"
    b = line[1] - m * (line[0])
    # Get interpolation object
    ix = np.arange(0, img.shape[1])
    iy = np.arange(0, img.shape[0])
    z = img[(img.shape[0] - 1 - iy[-1]):(img.shape[0] - iy[0]), ix[0]:ix[-1] + 1]

    if list(config.keys())[0] == "image" and len(z.shape) == 3:
        # If file is an image, take average of RGB values as point value
        z = np.mean(z, axis=2)

    int_pol = RegularGridInterpolator((iy, ix), z, method='linear', bounds_error=False, fill_value=None)
    if line[0] > line[2]:
        xarr = np.arange(int(line[2]), int(line[0]))
    else:
        xarr = np.arange(int(line[0]), int(line[2]))
    yarr = xarr * m + b
    if not xyswap:
        points = list(zip(yarr, xarr))
    else:
        points = list(zip(xarr, yarr))
    # Grab points from interpolation object
    data = int_pol(points)
    # If NetCDF and valid coordinate data is available, return that

    if list(config.keys())[0] == "netcdf":
        x_coord = config["netcdf"]["data"].coords[config["netcdf"][x_lab]].data
        y_coord = config["netcdf"]["data"].coords[config["netcdf"][y_lab]].data
        try:
            x_coord = x_coord.astype(float)
            y_coord = y_coord.astype(float)
            x_pix = min(abs(x_coord[:-1] - x_coord[1:]))
            y_pix = min(abs(y_coord[:-1] - y_coord[1:]))
            x = np.arange(x_coord.min(), x_coord.max() + x_pix, x_pix)
            y = np.arange(y_coord.min(), y_coord.max() + y_pix, y_pix)

            xcs = CubicSpline(range(len(x)), x)
            xarr = xcs(xarr)
            x_name = config["netcdf"]["x"]

            ycs = CubicSpline(range(len(y)), y)
            yarr = ycs(yarr)
            y_name = config["netcdf"]["y"]
        except ValueError:
            x_name = "x"
            y_name = "y"
    else:
        x_name = "x"
        y_name = "y"
    if line[0] > line[2] and xyswap:
        xarr = np.flip(xarr)
        yarr = np.flip(yarr)
        data = np.flip(data)
    if flipped:
        xarr = np.flip(xarr)
        yarr = np.flip(yarr)
        data = np.flip(data)
    if xyswap:
        data = {x_name: yarr, y_name: xarr, 'Cut': data}
    else:
        data = {x_name: xarr, y_name: yarr, 'Cut': data}
    data = {x_name: data[x_name].tolist(), y_name: data[y_name].tolist(), 'Cut': data['Cut'].tolist()}
    return data
