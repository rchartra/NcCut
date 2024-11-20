# SPDX-FileCopyrightText: 2024 University of Washington
#
# SPDX-License-Identifier: BSD-3-Clause

"""
Miscellaneous helper functions to support other widgets.

Provides reference to custom UI elements defined in nccut.kv file so they can be used in python scripts.
Contains error banner functionality, file management function, and transect taking function.

"""

import kivy
from kivy.graphics import Color, Rectangle
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.metrics import dp
from kivy.core.image import Image as CoreImage
import kivy.uix as ui
from functools import partial
from scipy.interpolate import RegularGridInterpolator, CubicSpline
import numpy as np
import math
import io
import warnings
import itertools
import xarray as xr
import matplotlib
from pathlib import Path
import tomli
import os
matplotlib.use('Agg')
import matplotlib.pyplot as plt


class RoundedButton(Button):
    """
    Code for this is in nccut.kv. Referenced here so it can be used in scripts.
    """
    pass


class BackgroundLabel(Label):
    """
    Code for this is in nccut.kv. Referenced here so it can be used in scripts.
    """
    pass


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
                                             "font_size": np.arange(8, 25)},
                       "tool_defaults": {"marker_width": np.arange(0, 401).astype(int)},
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


def sel_data(config):
    """
    Selects data from NetCDF file according to dimension and variable selections.

    Args:
        config: Dictionary of key details about NetCDF file as outlined in
            :meth:`nccut.netcdfconfig.NetCDFConfig.check_inputs`

    Returns:
        2D Dataset from NetCDF file according to selections transposed to (y, x).
    """
    # IMPORTANT: Numpy indexes (row, column) with (0, 0) at top left corner
    if config['z'] == 'N/A':
        # 2D NetCDF data
        ds = config['data'][config['var']].rename({config['y']: 'y', config['x']: 'x'})
        data = ds.sel(y=ds['y'], x=ds['x'])
    else:
        # 3D NetCDF data
        ds = config['data'][config['var']].rename({config['y']: 'y', config['x']: 'x', config['z']: 'z'})
        ds['z'] = ds['z'].astype(str)
        data = ds.sel(y=ds['y'], x=ds['x'], z=config['z_val'])
    return data.transpose('y', 'x')


def subset_around_transect(ds, points):
    """
    Determines a subset of the data with appropriate margins that surround the transect.

    If room is available around

    Args:
        ds: Data to be subset from. Either a DataArray (X and Y coordinates must be named "x" and "y") or a 2D array
        points: 4 element 1D array with coordinates of the two transect end points: [X1, Y1, X2, Y2]

    Returns:
        Subset of data, rescaled points [X1, Y1, X2, Y2], list of [Y, X] rescale factors
    """
    # Determine x, y bounds for subset area around transect
    ys_xs = [sorted([points[1], points[3]]), sorted([points[0], points[2]])]
    ys_xs = [c for cs in ys_xs for c in cs]
    if isinstance(ds, xr.DataArray):
        margins = [len(ds.coords["y"].data), len(ds.coords["x"].data)]
    else:
        margins = ds.shape
    # Include a buffer margin if possible for interpolating
    for i, p in enumerate(ys_xs):
        if i % 2 == 0:  # Minimums
            if p < 3:
                ys_xs[i] = int(np.floor(p))
            else:
                ys_xs[i] = int(np.floor(p)) - 3
        else:  # Maximums
            if p > margins[int(i / 3)] - 3:
                ys_xs[i] = int(np.floor(p))
            else:
                ys_xs[i] = int(np.floor(p)) + 3
    # Subset dataset around the transect
    if isinstance(ds, xr.DataArray):
        ds = ds.isel({"y": slice(ys_xs[0], ys_xs[1] + 1), "x": slice(ys_xs[2], ys_xs[3] + 1)})
    else:
        ds = ds[(margins[0] - 1 - ys_xs[1]): (margins[0] - ys_xs[0]), ys_xs[2]: ys_xs[3] + 1]

    points = [points[0] - ys_xs[2], points[1] - ys_xs[0], points[2] - ys_xs[2], points[3] - ys_xs[0]]

    scales = [ys_xs[0], ys_xs[2]]
    return ds, points, scales


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
    z = np.flipud(z)

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
        x = config["netcdf"]["data"].coords[config["netcdf"][x_lab]].data
        y = config["netcdf"]["data"].coords[config["netcdf"][y_lab]].data
        try:
            x = x.astype(float)
            xcs = CubicSpline(range(len(x)), x)
            xarr = xcs(xarr)
            x_name = config["netcdf"]["x"]

            y = y.astype(float)
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
