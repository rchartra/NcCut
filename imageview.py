"""
Class for main viewing window and interactive image.
"""

from kivy.graphics.transformation import Matrix
from kivy.uix.scatterlayout import ScatterLayout
from kivy.app import App
import kivy.uix as ui
from kivy.core.image import Image as CoreImage
from PIL import ImageEnhance
from PIL import Image as im
import numpy as np
import cmaps
import os
import io
import time


class ImageView(ScatterLayout):
    # Creates interactive image
    # Dragging is managed by ScatterLayout widget base
    def __init__(self, source, home, f_type, **kwargs):
        super(ImageView, self).__init__(**kwargs)
        self.source = source
        self.f_type = f_type
        self.home = home
        self.contrast = self.home.contrast
        self.byte = 0
        self.colormap = self.home.colormap
        if f_type == "netcdf":
            self.load_netcdf()
            self.im = CoreImage(self.byte, ext='png')
            self.size = self.im.size
        else:
            self.im = CoreImage(self.source)
            self.size = im.open(self.source).size
        self.pos = self.home.ids.view.pos

    gMode = False
    ScatterLayout.do_rotation = False
    ScatterLayout.do_scale = False

    def update_variable(self, variable):
        self.source = variable
        self.load_netcdf()
        self.im = CoreImage(self.byte, ext='png')
        self.size = self.im.size
        self.img.texture = self.im.texture
        self.img.reload()

    def update_colormap(self, colormap):
        self.colormap = colormap
        self.load_netcdf()
        self.im = CoreImage(self.byte, ext='png')
        self.size = self.im.size
        self.img.texture = self.im.texture
        self.img.reload()

    def update_contrast(self, contrast):
        self.contrast = contrast
        load = im.open(self.byte)
        enhancer = ImageEnhance.Contrast(load)
        img = enhancer.enhance(contrast)
        hold = io.BytesIO()
        img.save(hold, format="png")
        hold.seek(0)
        self.img.texture = CoreImage(io.BytesIO(hold.read()), ext="png").texture
        self.img.reload()

    def load_netcdf(self):
        n_data = (self.source - np.nanmin(self.source)) / (np.nanmax(self.source) - np.nanmin(self.source))
        n_data = np.nan_to_num(n_data, nan=1)
        n_data = (n_data * 255).astype(np.uint8)
        n_data = np.array(list(map(lambda n: list(map(lambda r: cmaps.all[self.colormap][r], n)), n_data)))
        n_data = (n_data * 255).astype(np.uint8)
        img = im.fromarray(n_data)

        # Applies contrast changes
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(self.contrast)

        temp = io.BytesIO()
        img.save(temp, format="png")
        temp.seek(0)
        self.byte = io.BytesIO(temp.read())

    def addImage(self):
        # Starts up image
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

    def on_touch_down(self, touch):
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