from kivy.graphics.transformation import Matrix
from kivy.uix.scatterlayout import ScatterLayout
import kivy.uix as ui


class ImageView(ScatterLayout):
    # Creates interactive image
    # Dragging is managed by ScatterLayout widget base
    def __init__(self, size, source, home, **kwargs):
        super(ImageView, self).__init__(**kwargs)
        self.source = source
        self.size = size
        self.home = home
        self.pos = self.home.ids.view.pos
        self.img = ui.image.Image(source=self.source)
        self.img.reload()
        self.add_widget(self.img)

    gMode = False
    ScatterLayout.do_rotation = False
    ScatterLayout.do_scale = False

    def addImage(self):
        # Starts up image
        self.img = ui.image.Image(source=self.source,  size=self.size, pos=self.parent.pos,
                         allow_stretch=True)

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