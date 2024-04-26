"""
Functionality for viewing window and interactive image.
"""
import time
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

    gMode = False
    ScatterLayout.do_rotation = False
    ScatterLayout.do_scale = False

    def font_adapt(self, font):
        print("Font: " + str(font))
        print("Current Back Font: " + str(self.back.font_size))

        self.back.font_size = font
        self.delete_line.font_size = font
        self.delete_point.font_size = font

    def load_file(self, source, f_type):
        # Loads file based on whether it's an image or netcdf file
        self.source = source
        self.f_type = f_type
        if f_type == "netcdf":
            self.load_netcdf()
            self.im = CoreImage(self.byte, ext='png')
            self.size = self.im.size
        else:
            self.im = CoreImage(self.source)
            self.size = im.open(self.source).size
        self.add_image()

    def edit_mode(self, *args):
        # Turns editing mode on if off and off if on
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
        # Turns dragging mode on if off and off if on
        if self.home.drag.text == "Drag Mode":
            self.home.drag.text = "Transect Mode"
            kivy.core.window.Window.set_system_cursor("arrow")
            self.home.transect.change_dragging(True)
        elif self.home.drag.text == "Transect Mode":
            self.home.drag.text = "Drag Mode"
            kivy.core.window.Window.set_system_cursor("crosshair")
            self.home.transect.change_dragging(False)

    def update_netcdf(self, new):
        # Reload netcdf image when netcdf settings are changed
        self.source = new
        self.load_netcdf()
        self.im = CoreImage(self.byte, ext='png')
        self.size = self.im.size
        self.img.texture = self.im.texture
        self.img.reload()

    def update_colormap(self, colormap):
        # Reload netcdf image when colormap is changed
        self.colormap = self.home.cmaps[colormap]
        self.load_netcdf()
        self.im = CoreImage(self.byte, ext='png')
        self.size = self.im.size
        self.img.texture = self.im.texture
        self.img.reload()

    def update_contrast(self, contrast):
        # Reload netcdf image when contrast is changed
        self.contrast = contrast
        self.load_netcdf()
        self.im = CoreImage(self.byte, ext='png')
        self.size = self.im.size
        self.img.texture = self.im.texture
        self.img.reload()

    def load_netcdf(self):
        # Create image from selected NetCDF data
        dat = self.source
        n_data = (dat - np.nanmin(dat)) / (np.nanmax(dat) - np.nanmin(dat))
        n_data = np.nan_to_num(n_data, nan=1)
        n_data = (n_data * 255).astype(np.uint8)
        img = cv2.applyColorMap(n_data, self.colormap)
        self.get_color_bar()

        # Applies contrast settings
        img = self.apply_contrast(img, self.contrast)
        is_success, img = cv2.imencode(".png", img)
        self.byte = io.BytesIO(img)

    def get_color_bar(self):
        # Create color bar image and format it
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
        self.home.update_color_bar(plot)

    def add_image(self):
        # Starts up image, im must exist and be a CoreImage or Image object (precede with load_file)
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
        # Perform contrast level adjustment to data
        f = 131 * (contrast + 127) / (127 * (131 - contrast))
        alpha_c = f
        gamma_c = 127 * (1 - f)
        out = cv2.addWeighted(data, alpha_c, data, 0, gamma_c)
        return out

    def flip_vertically(self):
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
        # Flip draggable image horizontally
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