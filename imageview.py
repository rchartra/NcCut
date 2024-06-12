"""
Functionality for viewing window and interactive image.

The dragability of the image is managed by the parent ScatterLayout class. This module
manages the scrolling, rotation, and flipping of the image. It also executes the creation of
and updates made to the image/dataset being displayed.
"""

import kivy
from kivy.graphics.transformation import Matrix
from kivy.uix.scatterlayout import ScatterLayout
import kivy.uix as ui
from kivy.core.image import Image as CoreImage
from PIL import Image as im
import numpy as np
import cv2
import io
import functions as func
import matplotlib.pyplot as plt


class ImageView(ScatterLayout):
    """
    Creation and management of the interactive image.

    Loads image, or if it's a NetCDF file it turns dataset into an image according to settings. Updates image as
    needed and manages the scrolling, flipping, and rotating of the image.

    Attributes:
        source: 2D array of dataset or image data to be loaded
        im: kivy.core.CoreImage made from data array
        home: Reference to root HomeScreen instance
        contrast: Int from -127 to 127, contrast value to use when making image from NetCDF file
        byte: io.BytesIO object containing image made from NetCDF dataset loaded in memory
        colormap: current colormap data to use from dictionary described in __init__ method f HomeScreen
        pos: Position of viewer. Used to properly place transect widgets on screen.
        editing: Boolean, whether in editing mode or not
        back: Back button for editing mode
        delete_line: Delete line button
        delete_point: Delete point button
        edit_widgets: List of widgets that must be added to screen when entering editing mode
        current: List to hold other widgets when they are replaced by editing mode widgets

        Inherits additional attributes from kivy.uix.scatterlayout.ScatterLayout (see kivy docs)
    """
    def __init__(self, home, **kwargs):
        """
        Initializes settings and defines editing mode buttons.

        Args:
            home: Reference to root HomeScreen reference
        """
        super(ImageView, self).__init__(**kwargs)
        self.source = None
        self.im = None
        self.home = home
        self.contrast = self.home.contrast
        self.byte = None
        self.colormap = self.home.cmaps[self.home.colormap]
        self.pos = self.home.ids.view.pos

        # Editing Mode widgets
        self.editing = False
        self.back = func.RoundedButton(text="Back", size_hint=(1, 0.1), text_size=self.size,
                                       halign='center', valign='center', font_size=self.home.font)
        self.back.bind(on_press=self.edit_mode)
        self.delete_line = func.RoundedButton(text="Delete Last Line", size_hint=(1, 0.1),
                                              font_size=self.home.font)
        self.delete_line.bind(on_press=lambda x: self.home.transect.del_line())
        self.delete_point = func.RoundedButton(text="Delete Last Point", size_hint=(1, 0.1),
                                               font_size=self.home.font)
        self.delete_point.bind(on_press=lambda x: self.home.transect.del_point())

        self.edit_widgets = [self.back, self.delete_line, self.delete_point]
        self.current = []

    # Turn off ScatterLayout functionality that conflicts with ImageView functionality
    ScatterLayout.do_rotation = False
    ScatterLayout.do_scale = False

    def font_adapt(self, font):
        """
        Update editing mode button font sizes.

        Args:
            font: Float, new font size
        """
        self.back.font_size = font
        self.delete_line.font_size = font
        self.delete_point.font_size = font

    def edit_mode(self, *args):
        """
        Turns editing mode on if off and off if on.

        When editing mode is being turned on, all sidebar buttons below 'Actions' label are added to
        a temporary holding list and then replaced with editing buttons. When editing mode is turned
        off, the editing buttons are removed and the original buttons are returned to the sidebar.

        Args:
            *args: Unused arguments passed to method when called.
        """
        if self.editing:
            for i in self.edit_widgets:
                if i in self.home.ids.sidebar.children:
                    self.home.ids.sidebar.remove_widget(i)
            for i in reversed(self.current):
                if i not in self.home.ids.sidebar.children:
                    self.home.ids.sidebar.add_widget(i, 1)
            self.editing = False
        else:
            self.current = self.home.ids.sidebar.children[1:self.home.ids.sidebar.children.index(self.home.action)]
            for i in self.current:
                if i in self.home.ids.sidebar.children:
                    self.home.ids.sidebar.remove_widget(i)
            for i in self.edit_widgets:
                if i not in self.home.ids.sidebar.children:
                    self.home.ids.sidebar.add_widget(i, 1)
            self.editing = True
        self.home.transect.change_dragging(self.editing)

    def drag_mode(self, *args):
        """
        Calls for transecting tool to turn dragging mode on if off and off if on

        Args:
            *args: Unused arguments passed to method when called.
        """
        if self.home.drag.text == "Drag Mode":
            self.home.drag.text = "Transect Mode"
            kivy.core.window.Window.set_system_cursor("arrow")
            self.home.transect.change_dragging(True)
        elif self.home.drag.text == "Transect Mode":
            self.home.drag.text = "Drag Mode"
            kivy.core.window.Window.set_system_cursor("crosshair")
            self.home.transect.change_dragging(False)

    def update_netcdf(self, new):
        """
        Reload netcdf image when netcdf data is changed.

        Args:
            new: New 2D array of dataset.
        """
        self.source = new
        self.load_netcdf()
        self.im = CoreImage(self.byte, ext='png')
        self.size = self.im.size
        self.img.texture = self.im.texture
        self.img.reload()

    def update_colormap(self, colormap):
        """
        Reload netcdf image when colormap is changed.

        Args:
            colormap: String, new colormap to use.
        """
        self.colormap = self.home.cmaps[colormap]
        self.load_netcdf()
        self.im = CoreImage(self.byte, ext='png')
        self.size = self.im.size
        self.img.texture = self.im.texture
        self.img.reload()

    def update_contrast(self, contrast):
        """
        Reload netcdf image when contrast is changed.

        Args:
            contrast: Int from -127 to 127, contrast value to use when making image from NetCDF file
        """
        self.contrast = contrast
        self.load_netcdf()
        self.im = CoreImage(self.byte, ext='png')
        self.size = self.im.size
        self.img.texture = self.im.texture
        self.img.reload()

    def load_netcdf(self):
        """
        Creates image from NetCDF dataset defined in self.source

        Normalizes data and then rescales it to between 0 and 255. Applies colormap and contrast settings
        and then calls for the creation of colorbar. Loads image into memory as io.BytesIO object so kivy
        can make image out of an array.
        """
        dat = self.source
        n_data = (dat - np.nanmin(dat)) / (np.nanmax(dat) - np.nanmin(dat))
        n_data = np.nan_to_num(n_data, nan=1)
        n_data = (n_data * 255).astype(np.uint8)
        img = cv2.applyColorMap(n_data, self.colormap)
        self.home.update_color_bar(self.get_color_bar())

        # Applies contrast settings
        img = self.apply_contrast(img, self.contrast)
        is_success, img = cv2.imencode(".png", img)
        self.byte = io.BytesIO(img)

    def get_color_bar(self):
        """
        Create color bar image according to colormap and dataset
        """
        c_arr = (np.arange(0, 256) * np.ones((10, 256))).astype(np.uint8)
        c_bar = cv2.applyColorMap(c_arr, self.colormap)
        c_bar = cv2.cvtColor(c_bar, cv2.COLOR_BGR2RGB)
        plt.figure(figsize=(10, 1))
        plt.imshow(c_bar)

        ax = plt.gca()
        ax.get_yaxis().set_visible(False)
        lab_arr = np.linspace(np.nanmin(self.source), np.nanmax(self.source), 256)
        lab_arr = ["{:.2e}".format(elem) for elem in lab_arr]
        ticks = [0, 50, 100, 150, 200, 250]
        ax.set_xticks(ticks=ticks, labels=[lab_arr[i] for i in ticks], fontsize=20)
        ax.xaxis.label.set_color('white')
        ax.tick_params(axis='x', colors='white')
        temp = io.BytesIO()
        plt.savefig(temp, facecolor=(0.2, 0.2, 0.2), bbox_inches='tight', format="png")
        temp.seek(0)
        plt.close()
        plot = ui.image.Image(source="", texture=CoreImage(io.BytesIO(temp.read()), ext="png").texture)
        return plot

    def add_image(self, source, f_type):
        """
        Creates UI Image element, loads it in viewer, and scales it to window size.

        Args:
            source: 2D array of dataset or image to be loaded
            f_type: String, 'netcdf' or 'image' according to file type
        """
        self.source = source
        if f_type == "netcdf":
            self.load_netcdf()
            self.im = CoreImage(self.byte, ext='png')
            self.size = self.im.size
        elif f_type == "image":
            self.im = CoreImage(self.source)
            self.size = im.open(self.source).size

        self.img = ui.image.Image(source="", texture=self.im.texture,  size=self.size, pos=self.parent.pos,
                         allow_stretch=True)
        self.add_widget(self.img)

        # Begin at max size where you can see entire image
        wsize = self.home.ids.view.size
        isize = self.bbox[1]
        if isize[0] >= wsize[0] or isize[1] >= wsize[1]:
            while self.bbox[1][0] >= wsize[0] or self.bbox[1][1] >= wsize[1]:
                mat = Matrix().scale(.9, .9, .9)
                self.apply_transform(mat)
        if isize[0] <= wsize[0] and isize[1] <= wsize[1]:
            while self.bbox[1][0] <= wsize[0] and self.bbox[1][1] <= wsize[1]:
                mat = Matrix().scale(1.1, 1.1, 1.1)
                self.apply_transform(mat)

        xco = wsize[0] / 2 - self.bbox[1][0] / 2
        self.pos = (xco, self.pos[1])

    def apply_contrast(self, data, contrast):
        """
        Perform contrast level adjustment to data

        Args:
            data: 2D array to which to apply contrast change
            contrast: Desired contrast value

        Return:
            Data with contrast adjusted
        """
        f = 131 * (contrast + 127) / (127 * (131 - contrast))
        alpha_c = f
        gamma_c = 127 * (1 - f)
        out = cv2.addWeighted(data, alpha_c, data, 0, gamma_c)
        return out

    def flip_vertically(self):
        """
        Flips image vertically
        """
        # Flip draggable image vertically
        m = Matrix()
        m.set(array=[
            [1.0, 0.0, 0.0, 0.0],
            [0.0, -1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]]
        )
        self.apply_transform(m, anchor=self.center)

    def flip_horizontally(self):
        """
        Flips image horizontally
        """
        m = Matrix()
        m.set(array=[
            [-1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]]
        )
        self.apply_transform(m, anchor=self.center)

    def rotate(self):
        """
        Rotates image 45 degrees counterclockwise
        """
        self.rotation += 45

    def on_touch_down(self, touch):
        """
        If touch is of a scrolling type zoom in or out of the image.
        
        Args:
            touch: MouseMotionEvent, see kivy docs for details
        """
        # Scroll to zoom
        if self.collide_point(*touch.pos):
            if touch.is_mouse_scrolling:
                if touch.button == 'scrolldown':
                    if self.scale < 10:
                        mat = Matrix().scale(1.1, 1.1, 1.1)
                        self.apply_transform(mat, anchor=touch.pos)
                elif touch.button == 'scrollup':
                    if self.scale > 0.1:
                        mat = Matrix().scale(.9, .9, .9)
                        self.apply_transform(mat, anchor=touch.pos)
            else:
                super(ImageView, self).on_touch_down(touch)