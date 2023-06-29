from singletransect import SingleTransect
from multitransect import MultiTransect
from marker import Marker
from multimarker import MultiMarker, Click
from cutview import HomeScreen
from PIL import Image as im
import numpy as np

# ==============================================
#  Test whether tools report the correct values
# ==============================================

# ------
# Image
# ------

home = HomeScreen()
home.nc = False
home.rgb = im.open("big.jpg").convert('RGB')
arr = np.asarray(home.rgb)

# Single Transect
# -----------------

# 0 degree angle cut

t = SingleTransect(False, home)

start = Click(100, 200)
end = Click(400, 200)

t.on_touch_down(start)
t.on_touch_down(end)

cut = t.ipGetPoints()

rows = np.shape(arr)[0] # numpy arrays are indexed by row, column NOT x, y
manual = np.ravel(np.mean(arr[rows - end.y-1:rows - start.y, start.x:end.x], axis=2))

# Max error: 0.0
print(max(manual - cut["Cut"]))

# 45 degree angle cut

t = SingleTransect(False, home)

start = Click(200, 200)
end = Click(400, 400)


t.on_touch_down(start)
t.on_touch_down(end)

cut = t.ipGetPoints()

rows = np.shape(arr)[0]
ix = np.arange(start.x, end.x)


manual = np.ravel(np.mean(arr[rows-ix-1, ix], axis=1))

# Max error: 0.0
print(max(manual - cut["Cut"]))

# 90 degree angle cut

t = SingleTransect(False, home)

start = Click(200, 100)
end = Click(200, 400)

t.on_touch_down(start)
t.on_touch_down(end)

cut = t.ipGetPoints()

rows = np.shape(arr)[0]
manual = np.ravel(np.mean(np.flip(arr[rows - end.y:rows - start.y, start.x:end.x+1]), axis=2))

# Max error: 0.0
print(max(manual - cut["Cut"]))

# Multiple Transect

# Marker

# Multiple Marker

# --------
# NC File
# --------

# Single Transect

# Multiple Transect

# Marker

# Multiple Marker


# Valid file names
