"""
This is the draggable and scalable plot image that is created when a user plots a transect over all z values for a 3D
NetCDF file.
"""

from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.image import Image
from kivy.core.image import Image as CoreImage
from kivy.graphics.transformation import Matrix
import matplotlib.pyplot as plt
import numpy as np
import io


class InteractivePlot(ScatterLayout):
    """
    Draggable and scalable plot image created from given transect data and constrained within the bounds of a viewing
    window.

    Args:
        data (arr): The 2D array of data to be plotted
        bounds (arr): Factors that define the maximum percentage of the layout space that the plot is allowed to take up
            in both width and height ([w_factor, h_factor])
        window: Reference to the PlotWindow object that is managing this plot
        byte: io.BytesIO object containing image made from data loaded in memory
        min_scale: The minimum scale the plot is able to have such that the plot always fills as much of the plotting
            widget as possible.
    """
    def __init__(self, array, z_coords, bounds, window, **kwargs):
        """
        Initializes the plot with given data and plotting window.

        Args:
            array (arr): The 2D array of data to be plotted
            z_coords (arr): 1D array of Z Coordinate data
            bounds (arr): Factors that define the maximum percentage of the layout space that the plot is allowed to take up
                in both width and height ([w_factor, h_factor])
            window: Reference to the PlotWindow object that is managing this plot
        """
        super(InteractivePlot, self).__init__(**kwargs)
        self.data = array
        try:
            self.z_coords = np.sort(z_coords.data.astype(float))
        except ValueError:
            self.z_coords = np.arange(0, len(z_coords))
        self.bounds = bounds
        self.window = window
        self.byte = None
        self.min_scale = None
        self.load_image()

    ScatterLayout.do_rotation = False
    ScatterLayout.do_scale = False

    def load_image(self):
        """
        Creates the kivy.uix.image.Image object to be placed on to this Scatter object and then rescales scatter to it's
        maximum possible size.
        """
        self.z_data_to_img()
        im = CoreImage(io.BytesIO(self.byte.read()), ext='png')
        self.size = im.size
        img = Image(source="", texture=im.texture, size=im.size, pos=self.pos)
        self.add_widget(img)
        bounds = [self.window.size[0] * self.bounds[0], self.window.size[1] * self.bounds[1]]
        r = min([bounds[i] / self.bbox[1][i] for i in range(len(bounds))])
        self.apply_transform(Matrix().scale(r, r, r))
        self.min_scale = self.scale

    def z_data_to_img(self):
        """
        Creates an image with a colormap applied from the supplied transect data over all z values. Stores result in
        memory as an io.BytesIO object.
        """
        n_data = (self.data - np.nanmin(self.data)) / (np.nanmax(self.data) - np.nanmin(self.data))

        x_grid, y_grid = np.meshgrid(self.z_coords, np.arange(0, n_data.shape[1]))
        plt.figure(frameon=False)
        plt.pcolormesh(y_grid, x_grid, n_data.T, cmap=self.window.colormap, shading="nearest")
        plt.gca().invert_yaxis()
        plt.axis('off')
        self.byte = io.BytesIO()
        plt.savefig(self.byte, format="png", bbox_inches='tight', pad_inches=0)
        self.byte.seek(0)
        plt.close()

    def transform_with_touch(self, touch):
        """
        Translates the scatter object when user clicks and drags the plot ensuring that it does not get dragged out
        of the bounds of the viewing window. Adapted from original ScatterLayout.transform_with_touch method, with
        multitouch functionality taken out.

        Args:
            touch: MouseMotionEvent, see kivy docs for details

        Returns:
            Whether a transformation has successfully taken place (even if transformation does not alter position of
            plot)
        """
        # Only one finger drags occur with NcCut
        dx = (touch.x - self._last_touch_pos[touch][0]) * self.do_translation_x
        dy = (touch.y - self._last_touch_pos[touch][1]) * self.do_translation_y
        dx = dx / self.translation_touches
        dy = dy / self.translation_touches
        pos = self.bbox[0]
        size = self.bbox[1]
        ub = self.window.ids.window_box.size
        d = [dx, dy]
        # Check translation in bounds and if not correct it so that it will be
        for i in range(len(d)):
            if pos[i] + d[i] > 0:
                d[i] = -pos[i]
            elif size[i] - ub[i] + pos[i] + d[i] < 0:
                d[i] = ub[i] - size[i] - pos[i]
            else:
                d[i] = d[i]
        tran = Matrix().translate(d[0], d[1], 0)
        self.apply_transform(tran)
        return True

    def on_touch_move(self, touch):
        """
        Calls for axes to update when plot is moved.

        Args:
            touch: MouseMotionEvent, see kivy docs for details
        """
        super(InteractivePlot, self).on_touch_move(touch)
        self.window.update_axes()

    def on_touch_down(self, touch):
        """
        If touch is of a scrolling type, zoom in or out of the image. Chooses scaling anchor to be as close to the user
        touch as possible without allowing the image to move beyond the bounds of the viewing window.

        Args:
            touch: MouseMotionEvent, see kivy docs for details
        """
        # Scroll to zoom
        if self.window.ids.window.collide_point(*touch.pos):
            if touch.is_mouse_scrolling:
                # Determine scale factor
                if touch.button == 'scrolldown' and self.scale < 20:
                    s = 1.05
                elif touch.button == 'scrollup' and self.scale > self.min_scale:
                    s_r = self.min_scale / self.scale
                    if s_r > 0.95:
                        s = s_r
                    else:
                        s = 0.95
                else:
                    s = 1
                mat = Matrix().scale(s, s, s)
                # Try anchoring at touch
                ub = self.window.ids.window_box.size
                fp, fs = self.see_future_pos_size(touch.pos, mat)
                if fp[0] <= 0 and fs[0] + fp[0] >= ub[0] and fp[1] <= 0 and fs[1] + fp[1] >= ub[1]:
                    # Use touch location if possible
                    a = touch.pos
                    self.apply_transform(mat, anchor=a)
                else:
                    # Apply transform, get back to as close to the original position as possible before out of bounds
                    old_pos = self.bbox[0]
                    self.pos = (0, 0)
                    self.apply_transform(mat)
                    s = self.bbox[1]
                    os = [-old_pos[0], abs(ub[0] - s[0] - old_pos[0]), -old_pos[1], abs(ub[1] - s[1] - old_pos[1])]
                    self.pos = (old_pos[0] + min(os[0:2]), old_pos[1] + min(os[2:]))
                self.window.update_axes()
            else:
                super(InteractivePlot, self).on_touch_down(touch)

    def see_future_pos_size(self, anchor, scale_mat):
        """
        Determine the resulting size and position of this scatter if the provided scale matrix is applied to
        this scatter at the provided anchor. The scale matrix is not actually applied.

        Args:
            anchor (tuple): (x, y) coordinates of the proposed anchor
            scale_mat: Proposed scale matrix

        Returns:
            Tuples of the resulting position (x, y) and the resulting size (w, h)
        """
        t = Matrix().translate(anchor[0], anchor[1], 0).multiply(scale_mat)
        t = t.multiply(Matrix().translate(-anchor[0], -anchor[1], 0))
        f = t.multiply(self.transform)
        fs = [f[0] / self.scale * self.bbox[1][i] for i in range(len(self.bbox[1]))]
        return (f[12], f[13]), (fs[0], fs[1])
