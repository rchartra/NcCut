"""
Class for main viewing window and interactive image.
"""
import time
import kivy
from kivy.graphics.transformation import Matrix
from kivy.uix.scatterlayout import ScatterLayout
import kivy.uix as ui
from kivy.core.image import Image as CoreImage
from PIL import ImageEnhance
from PIL import Image as im
import PIL
import numpy as np
import xarray as xr
import cv2
import io
import functions as func


class ImageView(ScatterLayout):
    # Creates interactive image
    # Dragging is managed by ScatterLayout widget base
    def __init__(self, home, **kwargs):
        super(ImageView, self).__init__(**kwargs)
        self.source = None
        self.f_type = None
        self.im = None
        self.home = home
        self.contrast = self.home.contrast
        self.byte = None
        self.colormap = self.home.cmaps[self.home.colormap]
        self.pos = self.home.ids.view.pos

        # Editing Mode
        self.editing = False
        self.back = func.RoundedButton(text="Back", size_hint=(1, 0.1), text_size=self.size,
                                       halign='center', valign='center', font_size=self.home.size[0] / 5)
        self.back.bind(on_press=self.edit_mode)
        self.delete_line = func.RoundedButton(text="Delete Last Line", size_hint=(1, 0.1),
                                              font_size=self.home.size[0] / 5)
        self.delete_line.bind(on_press=lambda x: self.home.transect.del_line())
        self.delete_point = func.RoundedButton(text="Delete Last Point", size_hint=(1, 0.1),
                                               font_size=self.home.size[0] / 5)
        self.delete_point.bind(on_press=lambda x: self.home.transect.del_point())

        self.edit_widgets = [self.back, self.delete_line, self.delete_point]
        self.current = []

    gMode = False
    ScatterLayout.do_rotation = False
    ScatterLayout.do_scale = False

    def load_file(self, source, f_type):
        T0 = time.time()
        t0 = time.time()
        self.source = source
        t1 = time.time()
        #print("setting source: " + str(t1 - t0))
        self.f_type = f_type
        if f_type == "netcdf":
            t0 = time.time()
            self.load_netcdf()
            t1 = time.time()
            #print("load_netcdf(): " + str(t1 - t0))
            t0 = time.time()
            self.im = CoreImage(self.byte, ext='png')
            t1 = time.time()
            #print("core image: " + str(t1 - t0))
            t0 = time.time()
            self.size = self.im.size
            t1 = time.time()
            #print("setting size: " + str(t1 - t0))
        else:
            self.im = CoreImage(self.source)
            self.size = im.open(self.source).size
        t0 = time.time()
        self.add_image()
        t1 = time.time()
        #print("add_image(): " + str(t1 - t0))
        T1 = time.time()
        #print("inner load_file(): " + str(T1 - T0))

    def edit_mode(self, *args):
        if self.editing:
            for i in self.edit_widgets:
                self.home.ids.sidebar.remove_widget(i)
            for i in reversed(self.current):
                self.home.ids.sidebar.add_widget(i, 1)
            self.editing = False
        else:
            self.current = self.home.ids.sidebar.children[1:self.home.ids.sidebar.children.index(self.home.action)]
            for i in self.current:
                self.home.ids.sidebar.remove_widget(i)
            for i in self.edit_widgets:
                self.home.ids.sidebar.add_widget(i, 1)
            self.editing = True
        self.home.transect.dragging = self.editing

    def drag_mode(self, *args):
        if self.home.drag.text == "Drag Mode":
            self.home.drag.text = "Transect Mode"
            kivy.core.window.Window.set_system_cursor("arrow")
            self.home.transect.dragging = True
        elif self.home.drag.text == "Transect Mode":
            self.home.drag.text = "Drag Mode"
            kivy.core.window.Window.set_system_cursor("crosshair")
            self.home.transect.dragging = False

    def update_netcdf(self, new):
        self.source = new
        self.load_netcdf()
        self.im = CoreImage(self.byte, ext='png')
        self.size = self.im.size
        self.img.texture = self.im.texture
        self.img.reload()

    def update_colormap(self, colormap):
        self.colormap = self.home.cmaps[colormap]
        self.load_netcdf()
        self.im = CoreImage(self.byte, ext='png')
        self.size = self.im.size
        self.img.texture = self.im.texture
        self.img.reload()

    def update_contrast(self, contrast):
        self.contrast = contrast
        self.load_netcdf()
        self.im = CoreImage(self.byte, ext='png')
        self.size = self.im.size
        self.img.texture = self.im.texture
        self.img.reload()

    def load_netcdf(self):
        t0 = time.time()
        dat = self.source
        n_data = (dat - np.nanmin(dat)) / (np.nanmax(dat) - np.nanmin(dat))
        t1 = time.time()
        #print("normalizing: " + str(t1 - t0))
        t0 = time.time()
        n_data = np.nan_to_num(n_data, nan=1)
        t1 = time.time()
        #print("nan finding: " + str(t1 - t0))
        t0 = time.time()
        n_data = (n_data * 255).astype(np.uint8)
        img = cv2.applyColorMap(n_data, self.colormap)
        t1 = time.time()
        #print("colormapping: " + str(t1 - t0))
        # Applies contrast changes
        img = self.apply_contrast(img, self.contrast)
        t0 = time.time()
        is_success, img = cv2.imencode(".png", img)
        self.byte = io.BytesIO(img)
        t1 = time.time()
        #print("saving img: " + str(t1 - t0))

    def add_image(self):
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

    def apply_contrast(self, data, contrast):
        f = 131 * (contrast + 127) / (127 * (131 - contrast))
        alpha_c = f
        gamma_c = 127 * (1 - f)
        out = cv2.addWeighted(data, alpha_c, data, 0, gamma_c)
        return out

    def flip_vertically(self):
        m = Matrix()
        m.set(array=[
            [1.0, 0.0, 0.0, 0.0],
            [0.0, -1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]]
        )
        self.apply_transform(m, anchor=self.center)

    def flip_horizontally(self):
        m = Matrix()
        m.set(array=[
            [-1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]]
        )
        self.apply_transform(m, anchor=self.center)

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