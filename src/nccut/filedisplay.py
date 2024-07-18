"""
Functionality for viewing window and interactive display.

This module manages the scrolling, rotation, and flipping of the image. It also executes the creation of
and updates made to the image/dataset being displayed. The dragability of the image is managed by the parent
ScatterLayout class. Manages the creation and deletion of tools.
"""

import kivy
from kivy.graphics.transformation import Matrix
from kivy.uix.scatterlayout import ScatterLayout
import kivy.uix as ui
from kivy.core.image import Image as CoreImage
from PIL import Image as im
import numpy as np
import cv2
import copy
import io
import nccut.functions as func
from nccut.multitransect import MultiTransect
from nccut.multimarker import MultiMarker
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


class FileDisplay(ScatterLayout):
    """
    Creation and management of the interactive display.

    If file is a NetCDF file it turns dataset into an image according to settings. Loads image and updates it when
    settings are changed. Also manages the scrolling, flipping, and rotating of the image.

    Attributes:
        config (dict): A dictionary holding info about the file necessary for loading, updating, and accessing data from
            the file. Highest level should have one key that is the name of the file type ("image" or "netcdf") whose
            value is the necessary configuration settings. For images, the config dictionary has form
            {"image": str(file_path)}. For a netcdf file the value is a dictionary of configuration values (see
            :meth:`nccut.netcdfconfig.NetCDFConfig.check_inputs` for structure of dictionary)
        f_type (str): File type being loaded ("image" or "netcdf")
        home: Reference to root :class:`nccut.homescreen.HomeScreen` instance
        pos (tuple): Position of viewer. Used to properly place transect widgets on screen.
        sidebar (list): Reference to list of sidebar buttons
        og_sidebar (list): Original state of sidebar before any tools added widgets
        im: kivy.core.CoreImage made from data array
        byte: io.BytesIO object containing image made from NetCDF dataset loaded in memory
        img: kivy.uix.image.Image UI element which displays the image over the scatter object
        tool: Reference to currently loaded tool
        nc_data: If file is a NetCDF file, actively loaded data array
        dragging (bool): Whether in dragging mode or not
        editing (bool): Whether in editing mode or not
        t_mode (bool): Whether a tool is currently loaded
        contrast (int): Int from -127 to 127, contrast value to use when making image from NetCDF file
        l_col (str): Line color for transect tools: 'Blue', 'Green' or 'Orange'
        cir_size (float): Circle size for transect tools
        cmaps (dict): Dictionary of colormap names mapping to colormap values from cv2
        colormap: current colormap data
        action_lbl: Actions label to be loaded when in transect mode
        drag_btn: Drag button to be loaded when in transect mode
        edit_btn: Edit button to be loaded when in transect mode
        back_btn: Back button for editing mode
        delete_line_btn: Delete line button
        delete_point_btn: Delete point button
        edit_widgets (list): List of widgets that must be added to screen when entering editing mode
        current (list): List to hold other widgets when they are replaced by editing mode widgets
    """
    def __init__(self, home, f_config, **kwargs):
        """
        Initializes settings and defines editing mode buttons.

        Args:
            home: Reference to root :class:`nccut.homescreen.HomeScreen` reference
            f_config (dict): A dictionary holding info about the file necessary for loading, updating, and accessing
                data from the file. Highest level should have one key that is the name of the file type ("image" or
                "netcdf") whose value is the necessary configuration settings. For images, the config dictionary has
                form {"image": str(file)}. For a netcdf file the value is a dictionary of configuration values (see
                :meth:`nccut.netcdfconfig.NetCDFConfig.check_inputs` for structure of dictionary)
        """
        super(FileDisplay, self).__init__(**kwargs)

        self.config = f_config
        self.f_type = list(f_config.keys())[0]
        self.home = home
        self.pos = self.home.ids.view.pos
        self.sidebar = self.home.ids.sidebar
        self.og_sidebar = copy.copy(self.home.ids.sidebar.children)

        self.im = None
        self.byte = None
        self.img = None
        self.tool = None
        self.nc_data = None

        self.dragging = False
        self.editing = False
        self.t_mode = False

        self.contrast = 1.0
        self.l_col = "Blue"
        self.cir_size = 10

        self.cmaps = {"Autumn": cv2.COLORMAP_AUTUMN, "Bone": cv2.COLORMAP_BONE, "Jet": cv2.COLORMAP_JET,
                      "Winter": cv2.COLORMAP_WINTER, "Rainbow": cv2.COLORMAP_RAINBOW, "Ocean": cv2.COLORMAP_OCEAN,
                      "Summer": cv2.COLORMAP_SUMMER, "Spring": cv2.COLORMAP_SPRING, "Cool": cv2.COLORMAP_COOL,
                      "HSV": cv2.COLORMAP_HSV, "Pink": cv2.COLORMAP_PINK, "Hot": cv2.COLORMAP_HOT,
                      "Parula": cv2.COLORMAP_PARULA, "Magma": cv2.COLORMAP_MAGMA, "Inferno": cv2.COLORMAP_INFERNO,
                      "Plasma": cv2.COLORMAP_PLASMA, "Viridis": cv2.COLORMAP_VIRIDIS, "Cividis": cv2.COLORMAP_CIVIDIS,
                      "Twilight": cv2.COLORMAP_TWILIGHT, "Twilight Shifted": cv2.COLORMAP_TWILIGHT_SHIFTED,
                      "Turbo": cv2.COLORMAP_TURBO, "Deep Green": cv2.COLORMAP_DEEPGREEN}
        self.colormap = self.cmaps['Viridis']

        # Action Widgets
        self.action_lbl = func.BackgroundLabel(text="Actions", size_hint=(1, 0.1),
                                               halign='center', valign='center', font_size=self.home.font)
        self.drag_btn = func.RoundedButton(text="Drag Mode", size_hint=(1, 0.1),
                                           halign='center', valign='center', font_size=self.home.font)
        self.drag_btn.bind(on_press=self.drag_mode)
        self.edit_btn = func.RoundedButton(text="Edit Mode", size_hint=(1, 0.1),
                                           halign='center', valign='center', font_size=self.home.font)
        self.edit_btn.bind(on_press=self.edit_mode)
        self.action_widgets = [self.action_lbl, self.drag_btn, self.edit_btn]

        # Editing Mode widgets
        self.back_btn = func.RoundedButton(text="Back", size_hint=(1, 0.1),
                                           halign='center', valign='center', font_size=self.home.font)
        self.back_btn.bind(on_press=self.edit_mode)
        self.delete_line_btn = func.RoundedButton(text="Delete Last Line", size_hint=(1, 0.1),
                                                  font_size=self.home.font)
        self.delete_line_btn.bind(on_press=lambda x: self.tool.del_line())
        self.delete_point_btn = func.RoundedButton(text="Delete Last Point", size_hint=(1, 0.1),
                                                   font_size=self.home.font)
        self.delete_point_btn.bind(on_press=lambda x: self.tool.del_point())

        self.edit_widgets = [self.back_btn, self.delete_line_btn, self.delete_point_btn]
        self.current = []

        self.load_image()

    # Turn off ScatterLayout functionality that conflicts with ImageView functionality
    ScatterLayout.do_rotation = False
    ScatterLayout.do_scale = False

    def font_adapt(self, font):
        """
        Update editing mode button font sizes.

        Args:
            font (float): New font size
        """
        self.action_lbl.font_size = font
        self.drag_btn.font_size = font
        self.edit_btn.font_size = font
        self.back_btn.font_size = font
        self.delete_line_btn.font_size = font
        self.delete_point_btn.font_size = font
        if self.t_mode:
            self.tool.font_adapt(font)

    def load_image(self):
        """
        Creates UI Image element, loads it in viewer, and scales it to window size.
        """

        if self.f_type == "netcdf":
            self.netcdf_to_image()
            self.im = CoreImage(self.byte, ext='png')
            self.size = self.im.size
        elif self.f_type == "image":
            self.im = CoreImage(self.config[self.f_type])
            self.size = im.open(self.config[self.f_type]).size

        self.img = ui.image.Image(source="", texture=self.im.texture, size=self.size, pos=self.home.ids.view.pos)
        self.add_widget(self.img)

        # Begin at max size where you can see entire image
        w_size = self.home.ids.view.size
        i_size = self.bbox[1]
        if i_size[0] >= w_size[0] or i_size[1] >= w_size[1]:
            while self.bbox[1][0] >= w_size[0] or self.bbox[1][1] >= w_size[1]:
                mat = Matrix().scale(.9, .9, .9)
                self.apply_transform(mat)
        if i_size[0] <= w_size[0] and i_size[1] <= w_size[1]:
            while self.bbox[1][0] <= w_size[0] and self.bbox[1][1] <= w_size[1]:
                mat = Matrix().scale(1.1, 1.1, 1.1)
                self.apply_transform(mat)

        xco = w_size[0] / 2 - self.bbox[1][0] / 2
        self.pos = (xco, self.pos[1])

    def manage_tool(self, t_type):
        """
        Manages the creation and deletion of each tool.

        If a tool is currently loaded, remove it, switch cursor to an arrow
        and clean up. If not, load indicated tool and switches cursor to a cross.

        Args:
            t_type (str): Tool type: 'transect' or 'transect_marker'
        """

        if not self.t_mode:
            # Opens a new tool
            for w in self.action_widgets:
                self.sidebar.add_widget(w, 1)
            kivy.core.window.Window.set_system_cursor("crosshair")
            if t_type == "transect":
                self.tool = MultiTransect(home=self.home)
            elif t_type == "transect_marker":
                self.tool = MultiMarker(home=self.home)
            self.add_widget(self.tool)
            self.t_mode = True
        else:
            kivy.core.window.Window.set_system_cursor("arrow")
            self.remove_widget(self.tool)
            self.drag_btn.text = "Drag Mode"
            self.editing = False
            self.reset_sidebar()
            self.t_mode = False

    def reset_sidebar(self):
        """
        Revert sidebar to pre-tool state
        """
        while self.sidebar.children != self.og_sidebar:
            self.sidebar.remove_widget(self.sidebar.children[1])

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
                if i in self.sidebar.children:
                    self.sidebar.remove_widget(i)
            for i in reversed(self.current):
                if i not in self.sidebar.children:
                    self.sidebar.add_widget(i, 1)
            self.editing = False
        else:
            if self.dragging:  # Can't be in both dragging and editing mode
                self.drag_mode()
            self.current = self.sidebar.children[1:self.sidebar.children.index(self.action_lbl)]
            for i in self.current:
                if i in self.sidebar.children:
                    self.sidebar.remove_widget(i)
            for i in self.edit_widgets:
                if i not in self.sidebar.children:
                    self.sidebar.add_widget(i, 1)
            self.editing = True
        self.tool.change_dragging(self.editing)

    def drag_mode(self, *args):
        """
        Calls for transecting tool to turn dragging mode on if off and off if on

        Args:
            *args: Unused arguments passed to method when called.
        """
        if not self.dragging:
            self.drag_btn.text = "Transect Mode"
            kivy.core.window.Window.set_system_cursor("arrow")
            self.tool.change_dragging(True)
            self.dragging = True
        else:
            self.drag_btn.text = "Drag Mode"
            kivy.core.window.Window.set_system_cursor("crosshair")
            self.tool.change_dragging(False)
            self.dragging = False

    def update_settings(self, setting, value):
        """
        Updates app settings depending on context of setting

        Args:
            setting (str): Name of setting being changed
            value: New setting value of appropriate data type
        """
        if setting == "l_color":
            self.l_col = value
            if self.t_mode:
                self.tool.update_l_col(value)
        elif setting == "cir_size":
            self.cir_size = float(value)
            if self.t_mode:
                self.tool.update_c_size(float(value))
        elif setting == "contrast":
            if self.f_type == "netcdf":
                self.contrast = float(value)
                self.update_netcdf()
        elif setting == "colormap":
            if self.f_type == "netcdf":
                self.colormap = self.cmaps[value]
                self.update_netcdf()
        elif setting == "variable":
            if self.f_type == "netcdf":
                self.config['netcdf']['var'] = value
                self.update_netcdf()
        elif setting == "depth":
            if self.f_type == "netcdf" and self.config['netcdf']['z'] != 'N/A':
                self.config['netcdf']['z_val'] = value
                self.update_netcdf()

    def update_netcdf(self):
        """
        Reload netcdf image when netcdf data is changed.
        """
        self.netcdf_to_image()
        self.im = CoreImage(self.byte, ext='png')
        self.size = self.im.size
        self.img.texture = self.im.texture
        self.img.reload()

    def netcdf_to_image(self):
        """
        Creates image from NetCDF dataset defined in :attr:`nccut.filedisplay.FileDisplay.f_config`

        Normalizes data and then rescales it to between 0 and 255. Applies colormap and contrast settings
        and then calls for the creation of colorbar. Loads image into memory as io.BytesIO object so kivy
        can make image out of an array.
        """
        self.nc_data = func.sel_data(self.config['netcdf'])
        n_data = (self.nc_data - np.nanmin(self.nc_data)) / (np.nanmax(self.nc_data) - np.nanmin(self.nc_data))
        n_data = np.nan_to_num(n_data, nan=1)
        n_data = (n_data * 255).astype(np.uint8)
        img = cv2.applyColorMap(n_data, self.colormap)
        self.update_color_bar(self.get_color_bar())

        # Applies contrast settings
        img = self.apply_contrast(img, self.contrast)
        is_success, img_b = cv2.imencode(".png", img)
        self.byte = io.BytesIO(img_b)

    def update_color_bar(self, colorbar):
        """
        Adds colorbar image to settings bar.

        Args:
            colorbar: kivy.uix.image.Image, colorbar graphic
        """
        if len(self.home.ids.colorbar.children) != 0:
            self.home.ids.colorbar.remove_widget(self.home.ids.colorbar.children[0])
        self.home.ids.colorbar.add_widget(colorbar)

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
        lab_arr = np.linspace(np.nanmin(self.nc_data), np.nanmax(self.nc_data), 256)
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

    def apply_contrast(self, data, contrast):
        """
        Perform contrast level adjustment to data

        Args:
            data: 2D array to which to apply contrast change
            contrast (int): Desired contrast value

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
        Flips display vertically
        """
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
        Flips display horizontally
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
        Rotates display 45 degrees counterclockwise
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
                super(FileDisplay, self).on_touch_down(touch)
