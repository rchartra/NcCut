import kivy
from kivy.graphics import Color, Rectangle
from kivy.uix.button import Button
from kivy.uix.label import Label
from functools import partial
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import copy
import re
from os.path import exists


class RoundedButton(Button):
    pass


def remove_alert(alert, home, *largs):
    home.remove_widget(alert)


def alert(text, home):
    screen = kivy.core.window.Window.size
    with home.canvas:
        Color(0.2, 0.2, 0.2)
        box = Rectangle(pos=(10, kivy.core.window.Window.size[1] - 60), size=(300, 50))
    aler = Label(text=text, size=home.size, pos=(-(screen[0] / 2) + 160, screen[1] / 2 - 35))
    home.add_widget(aler)
    kivy.clock.Clock.schedule_once(partial(remove_alert, aler, home), 2)
    kivy.clock.Clock.schedule_once(partial(home.canvas_remove, box), 2)


def check_file(fname, extension):

    if fname.find(".") >= 1:
        fname = fname[:fname.find(".")]
    if fname == "" or len(re.findall(r'[^A-Za-z0-9_\-/]', fname)) > 0:
        return False
    if "/" in fname:
        if not exists(fname[:fname.rfind("/")+1]):
            return False

    exist = True
    fcount = 0
    while exist:
        if exists(fname + extension):
            fcount += 1
            if fcount == 1:
                fname = fname + "(1)"
            else:
                fname = fname[:fname.find("(") + 1] + str(fcount) + ")"
        else:
            exist = False

    return fname


def plotdf(data, home):
    # General Plotting Code
    dat = copy.copy(data)
    if list(dat.keys())[0] == "Click X":
        dat.pop("Click X")
        dat.pop("Click Y")
        dat.pop("Width")
    if list(dat.keys())[0] == "Cut 1":
        df = pd.DataFrame()
        for i in dat.keys():
            df = pd.concat([df, pd.DataFrame(dat[i]["Cut"], columns=[i])], axis=1)
        x = np.asarray(df.index)
        axis = (x - x[0]) / (x[-1] - x[0])
        plt.plot(axis, df)
        plt.legend(df.columns, title="Legend", bbox_to_anchor=(1.05, 1))
    else:
        x = np.asarray(dat['x'])
        axis = (x - x[0]) / (x[-1] - x[0])
        plt.plot(axis, dat['Cut'])

    if home.nc:
        plt.ylabel(home.ds.capitalize())
    else:
        plt.ylabel("Mean RGB Value")
        plt.gca().set_ylim(ymin=0)
    plt.xlabel("Normalized Long Transect Distance")
    plt.tight_layout()
    plt.savefig("____.jpg")
    plt.close('all')
