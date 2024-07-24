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
from scipy.interpolate import RegularGridInterpolator
import numpy as np
import math
import re
from pathlib import Path


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
        2D array of data from NetCDF file.
    """
    # IMPORTANT: Numpy indexes (row, column) with (0, 0) at top left corner
    if config['z'] == 'N/A':
        # 2D NetCDF data
        ds = config['file'][config['var']].rename({config['y']: 'y', config['x']: 'x'})
        ds = ds.transpose('y', 'x')
        data = ds.sel(y=ds['y'], x=ds['x'])
    else:
        # 3D NetCDF data
        ds = config['file'][config['var']].rename({config['y']: 'y', config['x']: 'x', config['z']: 'z'})
        ds = ds.transpose('y', 'x', 'z')
        ds['z'] = ds['z'].astype(str)
        data = ds.sel(y=ds['y'], x=ds['x'], z=config['z_val'])
    return np.flip(data.data, 0)


def ip_get_points(line, curr, nc):
    """
    Creates a data frame containing x, y, and value of points on transect line

    From end points finds points of line connecting them. Interpolates higher resolution version of
    relevant section of data set, and then grabs data values at each line point.

    Args:
        line: 4 element 1D array with coordinates of the two transect end points: [X1, Y1, X2, Y2]
        curr: 2D indexable array of current dataset loaded in viewer
        nc (bool): Whether data is from a NetCDF file
    Returns:
        Dictionary with three keys:
            'x': 1D array of x-coordinates of transect points
            'y': 1D array of y-coordinates of transect points
            'Cut': 1D array of data values at each point along line connecting end points
    """

    # If angle of line is > 45 degrees will swap x and y to increase accuracy
    data = []
    xyswap = False

    img = np.asarray(curr)

    # Always read from left point to right
    if line[0] > line[2]:
        line = [line[2], line[3], line[0], line[1]]

    # Get interpolation object

    # Get x values
    # Include margin if possible
    if int(line[0]) < 3:
        x_start = line[0]
    else:
        x_start = line[0] - 3
    if int(line[2]) > img.shape[1] - 4:
        x_end = line[2]
    else:
        x_end = line[2] + 4
    ix = np.arange(int(x_start), int(x_end))

    # Get y values increasing in value w/o changing og object
    # Include margin if possible

    if line[1] > line[3]:
        y_points = [line[3], line[1]]
    else:
        y_points = [line[1], line[3]]
    if int(y_points[0]) < 3:
        y_start = y_points[0]
    else:
        y_start = y_points[0] - 3
    if int(y_points[1]) > img.shape[1] - 4:
        y_end = y_points[1]
    else:
        y_end = y_points[1] + 4
    iy = np.arange(int(y_start), int(y_end))

    # Get line slope
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
    b = line[1] - m * (line[0])
    z = img[-(iy[-1] + 1):-(iy[0]), ix[0]:ix[-1] + 1]
    if not nc and len(z.shape) == 3:
        # If image, take average of RGB values as point value
        z = np.mean(z, axis=2)
    z = np.flipud(z)

    # numpy arrays are indexed by row, column NOT x, y, but interp object does do x y
    int_pol = RegularGridInterpolator((iy, ix), z, method='linear')

    if line[0] > line[2]:
        xarr = np.arange(int(line[2]), int(line[0]))
    else:
        xarr = np.arange(int(line[0]), int(line[2]))
    yarr = xarr * m + b

    # Grab points from interpolation object
    for i in range(0, xarr.size):
        if not xyswap:
            data.append(int_pol([yarr[i], xarr[i]])[0])
        else:
            data.append(int_pol([xarr[i], yarr[i]])[0])
    if xyswap:
        data = {'x': yarr, 'y': xarr, 'Cut': data}
    else:
        data = {'x': xarr, 'y': yarr, 'Cut': data}
    data = {'x': data['x'].tolist(), 'y': data['y'].tolist(), 'Cut': data['Cut']}

    return data
