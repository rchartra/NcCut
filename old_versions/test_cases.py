from singletransect import SingleTransect
from multitransect import MultiTransect
from marker import Marker
from multimarker import MultiMarker, Click
from homescreen import HomeScreen
from cutview import cutview
from PIL import Image as im
from kivy.graphics import Line
import numpy as np
import xarray as xr
import pytest
import json

# ==============================================
#  Test whether tools report the correct values
# ==============================================

@pytest.fixture
def clicks_zero_degree():
    return [Click(1000, 200), Click(1200, 200)]


@pytest.fixture
def clicks_45_degree():
    return [Click(1000, 200), Click(1200, 400)]


@pytest.fixture
def clicks_90_degree():
    return [Click(1000, 100), Click(1000, 400)]


@pytest.fixture
def home_fixture():
    home = HomeScreen()
    home.data = xr.open_dataset("../support/example.nc")["Vorticity"].data
    home.rgb = im.open("../support/example.jpg").convert('RGB')
    return home


# ----------------
# Single Transect
# ----------------


# Image
# -----------------

# 0 degree angle cut


def test_single_zero(home_fixture, clicks_zero_degree):

    home_fixture.nc = False
    t = SingleTransect(False, home_fixture)
    start = clicks_zero_degree[0]
    end = clicks_zero_degree[1]

    t.on_touch_down(start)
    t.on_touch_down(end)

    cut = t.ipGetPoints()
    arr = np.asarray(home_fixture.rgb)

    rows = np.shape(arr)[0] # numpy arrays are indexed by row, column NOT x, y
    manual = np.ravel(np.mean(arr[rows - end.y-1:rows - start.y, start.x:end.x], axis=2))

    assert max(manual - cut["Cut"]) == 0

# 45 degree angle cut


def test_single_45(home_fixture, clicks_45_degree):
    home_fixture.nc = False
    t = SingleTransect(False, home_fixture)
    start = clicks_45_degree[0]
    end = clicks_45_degree[1]
    t.on_touch_down(start)
    t.on_touch_down(end)

    cut = t.ipGetPoints()

    arr = np.asarray(home_fixture.rgb)
    rows = np.shape(arr)[0]
    ix = np.arange(start.x, end.x)
    iy = np.arange(start.y, end.y)

    manual = np.ravel(np.mean(arr[rows-iy-1, ix], axis=1))

    assert max(manual - cut["Cut"]) == 0

# 90 degree angle cut


def test_single_90(home_fixture, clicks_90_degree):
    home_fixture.nc = False
    t = SingleTransect(False, home_fixture)
    start = clicks_90_degree[0]
    end = clicks_90_degree[1]

    t.on_touch_down(start)
    t.on_touch_down(end)

    cut = t.ipGetPoints()
    arr = np.asarray(home_fixture.rgb)

    rows = np.shape(arr)[0]
    manual = np.ravel(np.mean(np.flip(arr[rows - end.y:rows - start.y, start.x:end.x+1]), axis=2))

    assert max(manual - cut["Cut"]) == 0

# NC File
# --------


def test_single_zero_nc(home_fixture, clicks_zero_degree):

    home_fixture.nc = True
    t = SingleTransect(False, home_fixture)
    start = clicks_zero_degree[0]
    end = clicks_zero_degree[1]

    t.on_touch_down(start)
    t.on_touch_down(end)

    cut = t.ipGetPoints()
    arr = np.asarray(home_fixture.data)

    rows = np.shape(arr)[0]  # numpy arrays are indexed by row, column NOT x, y
    manual = arr[rows - end.y - 1:rows - start.y, start.x:end.x][0]

    assert max(manual - cut["Cut"]) == 0


def test_single_45_nc(home_fixture, clicks_45_degree):

    home_fixture.nc = True
    t = SingleTransect(False, home_fixture)
    start = clicks_45_degree[0]
    end = clicks_45_degree[1]

    t.on_touch_down(start)
    t.on_touch_down(end)

    cut = t.ipGetPoints()
    arr = np.asarray(home_fixture.data)

    rows = np.shape(arr)[0]  # numpy arrays are indexed by row, column NOT x, y

    ix = np.arange(start.x, end.x)
    iy = np.arange(start.y, end.y)

    manual = arr[rows - iy - 1, ix]

    assert max(manual - cut["Cut"]) == 0


def test_single_90_nc(home_fixture, clicks_90_degree):
    home_fixture.nc = True
    t = SingleTransect(False, home_fixture)
    start = clicks_90_degree[0]
    end = clicks_90_degree[1]

    t.on_touch_down(start)
    t.on_touch_down(end)

    cut = t.ipGetPoints()
    arr = np.asarray(home_fixture.data)

    rows = np.shape(arr)[0]  # numpy arrays are indexed by row, column NOT x, y
    manual = np.ravel(np.flip(arr[rows - end.y:rows - start.y, start.x:end.x+1]))
    print(cut["Cut"])
    print(manual)

    assert max(manual - cut["Cut"]) == 0

# ------------------
# Multiple Transect
# ------------------


def test_multi_transect(home_fixture):
    t = MultiTransect(home_fixture)
    t.test_mode()
    clicks = [Click(20, 120), Click(50, 150), Click(80, 180), Click(110, 210)]
    for i in clicks:
        t.on_touch_down(i)
    assert len(t.lines) == 2


# -------
# Marker
# -------


def test_marker(home_fixture):
    t = Marker(False, home_fixture)
    t.update_width(50)
    line = Line(points=[50, 50, 100, 100])
    coords = np.array(t.get_orthogonal(line))
    assert max(coords - [50, 100, 100, 50]) == 0

# -----------------------
# Multiple Marker Upload
# -----------------------


def test_marker_upload(home_fixture):
    t = MultiMarker(home_fixture)
    dat = json.load(open("../support/example_markers.json"))
    t.upload_data(dat)

# Valid file names
