"""
Helper functions to support other widgets.
"""

import matplotlib.pyplot as plt
import kivy
from kivy.graphics import Color, Rectangle
from kivy.uix.button import Button
from kivy.uix.label import Label
from functools import partial
from scipy import interpolate
import pandas as pd
import numpy as np
import math
import copy
import re
from os.path import exists
from pathlib import Path


class RoundedButton(Button):
    # Code for this is in cutview.kv. Referenced here so it can be used in scripts.
    pass


class BackgroundLabel(Label):
    # Code for this is in cutview.kv. Referenced here so it can be used in scripts.
    pass


def remove_alert(alert, home, *largs):
    # Removes alert banner
    home.remove_widget(alert)


def alert(text, home):
    # Creates alert banner with given text, schedules it to be removed after 2 seconds.
    screen = kivy.core.window.Window.size
    with home.canvas:
        Color(0.2, 0.2, 0.2)
        box = Rectangle(pos=(10, kivy.core.window.Window.size[1] - 60), size=(300, 50))
    aler = Label(text=text, size=home.size, pos=(-(screen[0] / 2) + 160, screen[1] / 2 - 35))
    home.add_widget(aler)
    kivy.clock.Clock.schedule_once(partial(remove_alert, aler, home), 2)
    kivy.clock.Clock.schedule_once(partial(home.canvas_remove, box), 2)


def check_file(path, fname, extension):
    # Checks that a given file name is valid and if file already exists takes measures to avoid overwriting.
    # If a directory is part of the file path checks that the directory exists.
    if fname.find(".") >= 1:
        fname = fname[:fname.find(".")]
    if fname == "" or len(re.findall(r'[^A-Za-z0-9_\-/:]', fname)) > 0:
        return False
    if "/" in fname:
        if not Path.exists(path / fname[:fname.rfind("/")+1]):
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


def plotdf(data, home):
    # Create plots
    dat = copy.copy(data)
    plot_dat = {}
    if list(dat.keys())[0][0:6] == "Marker":
        for marker in list(dat.keys()):
            for cut in list(dat[marker].keys()):
                plot_dat["M" + marker[-1] + " " + cut] = dat[marker][cut]["Cut"]
    elif list(dat.keys())[0][0:3] == "Cut":
        for cut in list(dat.keys()):
            plot_dat[cut] = dat[cut]["Cut"]
    df = pd.DataFrame.from_dict(dict([(k, pd.Series(v)) for k, v in plot_dat.items()]))
    x = np.asarray(df.index)
    axis = (x - x[0]) / (x[-1] - x[0])
    plt.plot(axis, df)
    plt.legend(df.columns, title="Legend", bbox_to_anchor=(1.05, 1))

    if home.nc:
        plt.ylabel(home.netcdf['var'].capitalize())
    else:
        plt.ylabel("Mean RGB Value")
        plt.gca().set_ylim(ymin=0)
    plt.xlabel("Normalized Long Transect Distance")
    plt.tight_layout()
    plt.savefig("____.jpg")
    plt.close('all')


def ip_get_points(points, curr, nc):
    # Creates a data frame containing x, y, and value of points on transect line
    # If angle of line is > 45 degrees will swap x and y to still get an accurate answer
    r = 0
    data = []
    xyswap = False
    # Gather data as array
    img = curr
    line = points
    # Always read from left point to right
    if line[0] > line[2]:
        line = [line[2], line[3], line[0], line[1]]

    # Get interpolation object

    # Get x values
    ix = np.arange(int(line[0] - 3), int(line[2] + 4))
    # Get y values increasing in value w/o changing og object
    if line[1] > line[3]:
        iy = np.arange(int(line[3] - 3), int(line[1] + 4))
    else:
        iy = np.arange(int(line[1] - 3), int(line[3] + 4))
    # Get line slope
    if line[2] - line[0] == 0:
        m = (line[3] - line[1]) / .001
    else:
        m = (line[3] - line[1]) / (line[2] - line[0])
    # If slope greater than 45 deg swap xy
    if abs(math.atan(m)) > (math.pi / 4):
        xyswap = True
        line = [line[1], line[0], line[3], line[2]]
        # Recalculate slope with new order
        if line[2] - line[0] == 0:
            m = (line[3] - line[1]) / .001
        else:
            m = (line[3] - line[1]) / (line[2] - line[0])
    b = line[1] - m * (line[0])
    imgA = np.asarray(img)
    z = imgA[-(iy[-1] + 1):-(iy[0]), ix[0]:ix[-1] + 1]
    if not nc:
        # If image, take average of RGB values as point value
        z = np.mean(z, axis=2)
    z = np.flipud(z)
    # numpy arrays are indexed by row, column NOT x, y, but interp object does do x y
    int_pol = interpolate.RegularGridInterpolator((iy, ix), z, method='linear')

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
