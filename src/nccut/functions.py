"""
Miscellaneous helper functions to support other widgets.

Provides reference to custom UI elements defined in nccut.kv file so they can be used in python scripts.
Contains error banner functionality, file management function, and transect taking function.

"""

import kivy
from kivy.graphics import Color, Rectangle
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.metrics import dp
from functools import partial
from scipy.interpolate import RegularGridInterpolator, CubicSpline
import numpy as np
import math
import re
from pathlib import Path
import xarray as xr


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
        text: String of alert banner message
        home: Active :class:`nccut.homescreen.HomeScreen` reference
    """

    screen = kivy.core.window.Window.size
    with home.canvas:
        Color(0.2, 0.2, 0.2)
        box = Rectangle(pos=(10, kivy.core.window.Window.size[1] - 60), size=(300, 50))
    aler = Label(text=text, size=home.size, pos=(-(screen[0] / 2) + 160, screen[1] / 2 - 35))
    home.add_widget(aler)
    kivy.clock.Clock.schedule_once(partial(remove_alert, aler, home), 2)
    kivy.clock.Clock.schedule_once(partial(home.canvas_remove, box), 2)


def check_file(path, fname, extension):
    """
    Checks if a filename is valid and prevents overwriting.

    Checks a file name doesn't have any problematic characters. If file name is a file path
    ensures that the directories exists. If a file name is the same as one that already
    exists it adds a (#) to avoid overwriting existing file.

    Args:
        path: pathlib.Path object of current output directory
        fname (str): User proposed file name
        extension (str): File extension for file type being created

    Returns:
        If all checks are passed the file name is returned, possibly with added (#). If checks aren't passed
        returns False.
    """
    if fname.find(".") >= 1:
        fname = fname[:fname.find(".")]
    if fname == "" or len(re.findall(r'[^A-Za-z0-9_\-/:]', fname)) > 0:
        return False
    if "/" in fname:
        if not Path.exists(path / fname[:fname.rfind("/") + 1]):
            return False

    exist = True
    fcount = 0
    while exist:
        if Path.exists(path / (fname + extension)):
            fcount += 1
            if fcount == 1:
                fname = fname + "(1)"
            else:
                fname = fname[:fname.find("(") + 1] + str(fcount) + ")"
        else:
            exist = False

    return fname


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
        ds = config['file'][config['var']].rename({config['y']: 'y', config['x']: 'x'})
        data = ds.sel(y=ds['y'], x=ds['x'])
    else:
        # 3D NetCDF data
        ds = config['file'][config['var']].rename({config['y']: 'y', config['x']: 'x', config['z']: 'z'})
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
    img = np.asarray(curr)
    # Always read from left point to right
    if line[0] > line[2]:
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
        x = config["netcdf"]["file"].coords[config["netcdf"][x_lab]].data
        y = config["netcdf"]["file"].coords[config["netcdf"][y_lab]].data
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

    if xyswap:
        data = {x_name: yarr, y_name: xarr, 'Cut': data}
    else:
        data = {x_name: xarr, y_name: yarr, 'Cut': data}
    data = {x_name: data[x_name].tolist(), y_name: data[y_name].tolist(), 'Cut': data['Cut'].tolist()}
    return data
