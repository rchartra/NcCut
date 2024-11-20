# SPDX-FileCopyrightText: 2024 University of Washington
#
# SPDX-License-Identifier: BSD-3-Clause

"""
Functionality for viewing window and interactive display.

This module manages the scrolling, rotation, and flipping of the image. It also executes the creation of
and updates made to the image/dataset being displayed. The dragability of the image is managed by the parent
ScatterLayout class. Manages the creation and deletion of tools.
"""

import kivy
from kivy.graphics.transformation import Matrix
from kivy.uix.scatterlayout import ScatterLayout
from kivy.core.window import Window
import kivy.uix as ui
from kivy.core.image import Image as CoreImage
from kivy.metrics import dp
from PIL import Image as im
from PIL import ImageEnhance
import numpy as np
import matplotlib.pyplot as plt
import io
import warnings
import nccut.functions as func
from nccut.multimarker import MultiMarker
from nccut.multichain import MultiChain


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
        resized (bool): Whether the image has been resized to fit in the viewer window
        contrast (int): Int from -127 to 127, contrast value to use when making image from NetCDF file
        l_col (str): Line color for transect tools: 'Blue', 'Green' or 'Orange'
        cir_size (float): Circle size for transect tools
        cmaps (dict): Dictionary of colormap names mapping to colormap values from cv2
        colormap: current colormap data
        btn_height: Height for buttons in sidebar which adapts to font size
        transect_chain_btn: Transect Chain button which opens Transect Chain tool
        transect_marker_btn: Transect Marker button which opens Transect Marker tool
        initial_side_bar (list): List of sidebar buttons in 'Tools' sidebar menu
        drag_btn: Drag button to be loaded when in transect mode
        edit_btn: Edit button to be loaded when in transect mode
        close_tool_btn: Button to close currently loaded tool
        action_widgets: Initial list of widgets in Actions menu, not including any widgets added by the tool
        tool_action_widgets: List of widgets in Actions menu at any given moment
        tran_mode_btn: Button to close Drag Mode
        back_btn: Back button for editing mode
        delete_line_btn: Delete line button
        delete_point_btn: Delete point button
        edit_widgets (list): List of widgets that must be added to screen when entering editing mode
    """
    def __init__(self, home, f_config, g_config, t_config, **kwargs):
        """
        Initializes settings and defines editing mode buttons.

        Args:
            home: Reference to root :class:`nccut.homescreen.HomeScreen` reference
            f_config (dict): A dictionary holding info about the file necessary for loading, updating, and accessing
                data from the file. Highest level should have one key that is the name of the file type ("image" or
                "netcdf") whose value is the necessary configuration settings. For images, the config dictionary has
                form {"image": str(file)}. For a netcdf file the value is a dictionary of configuration values (see
                :meth:`nccut.netcdfconfig.NetCDFConfig.check_inputs` for structure of dictionary)
            g_config (dict): Dictionary holding initial contrast value, line color, colormap, and circle size
            t_config (dict): Dictionary holding tool configurations: default marker width
        """
        super(FileDisplay, self).__init__(**kwargs)

        self.config = f_config
        self.default_marker_width = t_config["marker_width"]
        self.f_type = list(f_config.keys())[0]
        self.home = home
        self.sidebar = self.home.ids.sidebar

        self.im = None
        self.byte = None
        self.img = None
        self.tool = None
        self.nc_data = None

        self.dragging = False
        self.editing = False
        self.t_mode = False
        self.resized = False

        self.contrast = func.contrast_function(g_config["contrast"])
        self.l_col = g_config["line_color"]
        self.cir_size = g_config["circle_size"]

        self.cmaps = plt.colormaps()[:87]
        self.colormap = g_config["colormap"]
        self.btn_height = dp(20) + self.home.font
        # Initial Sidebar Widgets
        self.transect_chain_btn = func.RoundedButton(text="Transect Chain", size_hint_y=None, height=self.btn_height,
                                                     font_size=self.home.font)
        self.transect_chain_btn.bind(on_press=lambda x: self.transect_btn("transect_chain"))

        self.transect_marker_btn = func.RoundedButton(text="Transect Marker", size_hint_y=None, height=self.btn_height,
                                                      font_size=self.home.font)
        self.transect_marker_btn.bind(on_press=lambda x: self.transect_btn("transect_marker"))
        self.initial_side_bar = [self.transect_chain_btn, self.transect_marker_btn]

        # Action Widgets
        self.drag_btn = func.RoundedButton(text="Drag Mode", size_hint_y=None, height=self.btn_height,
                                           halign='center', valign='center', font_size=self.home.font)
        self.drag_btn.bind(on_press=self.drag_mode)
        self.edit_btn = func.RoundedButton(text="Edit Mode", size_hint_y=None, height=self.btn_height,
                                           halign='center', valign='center', font_size=self.home.font)
        self.edit_btn.bind(on_press=self.edit_mode)
        self.close_tool_btn = func.RoundedButton(text="Close Tool", size_hint_y=None, height=self.btn_height,
                                                 halign='center', valign='center', font_size=self.home.font)
        self.close_tool_btn.bind(on_press=self.close_tool)
        self.action_widgets = [self.close_tool_btn, self.drag_btn, self.edit_btn]
        self.tool_action_widgets = self.action_widgets
        # Drag Mode Widgets
        self.tran_mode_btn = func.RoundedButton(text="Transect Mode", size_hint_y=None, height=self.btn_height,
                                                halign='center', valign='center', font_size=self.home.font)
        self.tran_mode_btn.bind(on_press=self.drag_mode)

        # Editing Mode widgets
        self.back_btn = func.RoundedButton(text="Back", size_hint_y=None, height=self.btn_height,
                                           halign='center', valign='center', font_size=self.home.font)
        self.back_btn.bind(on_press=self.edit_mode)
        self.delete_line_btn = func.RoundedButton(text="Delete Last Line", size_hint_y=None, height=self.btn_height,
                                                  font_size=self.home.font)
        self.delete_line_btn.bind(on_press=lambda x: self.tool.del_line())
        self.delete_point_btn = func.RoundedButton(text="Delete Last Point", size_hint_y=None, height=self.btn_height,
                                                   font_size=self.home.font)
        self.delete_point_btn.bind(on_press=lambda x: self.tool.del_point())

        self.edit_widgets = [self.back_btn, self.delete_line_btn, self.delete_point_btn]

        self.load_image()
        Window.bind(on_key_down=self.on_key)

    # Turn off ScatterLayout functionality that conflicts with functionality
    ScatterLayout.do_rotation = False
    ScatterLayout.do_scale = False

    def on_key(self, *args):
        key_ascii = args[1]
        if key_ascii == 27 and self.tool and not self.home.plot_popup.is_open:
            self.tool.del_line()

    def font_adapt(self, font):
        """
        Update editing mode button and color bar font sizes.

        Args:
            font (float): New font size
        """
        self.back_btn.font_size = font
        self.delete_line_btn.font_size = font
        self.delete_point_btn.font_size = font
        if self.f_type == "netcdf":
            self.home.update_colorbar(func.get_color_bar(self.colormap, self.nc_data, (0.1, 0.1, 0.1), "white", font * 2.5))
        if self.t_mode:
            self.tool.font_adapt(font)

    def load_image(self):
        """
        Creates UI Image element, loads it in viewer, and scales it to window size.
        """
        if self.f_type == "netcdf":
            self.netcdf_to_image()
            self.byte.seek(0)
            self.im = CoreImage(self.byte, ext='png')
            self.size = self.im.size
        elif self.f_type == "image":
            self.im = CoreImage(self.config[self.f_type])
            self.size = im.open(self.config[self.f_type]).size
        self.img = ui.image.Image(source="", texture=self.im.texture, size=self.size, pos=self.pos)
        self.home.ids.view.bind(size=self.resize_to_fit)
        self.add_widget(self.img)
        self.home.populate_dynamic_sidebar(self.initial_side_bar, "Tools")
        # Necessary for when viewer doesn't change size on file load (image -> image)
        self.resize_to_fit(False)
        self.home.font_adapt()

    def resize_to_fit(self, *args):
        """
        Resizes image to be just large enough to fill viewer screen. Method is bound to size property but only resizes
        on initial size change

        Args:
            args: Two element list of object and it's size
        """
        if not self.resized:
            bounds = self.home.ids.view.size
            r = min([bounds[i] / self.bbox[1][i] for i in range(len(bounds))])
            self.apply_transform(Matrix().scale(r, r, r))
            xco = bounds[0] / 2 - self.bbox[1][0] / 2
            self.pos = (xco, self.pos[1])
            if args[0]:
                self.resized = True

    def transect_btn(self, t_type):
        """
        Manages the creation and deletion of each tool.

        If a tool is currently loaded, remove it, switch cursor to an arrow
        and clean up. If not, load indicated tool and switches cursor to a cross.

        Args:
            t_type (str): Tool type: 'transect_chain' or 'transect_marker'
        """

        if not self.t_mode:
            # Opens a new tool
            kivy.core.window.Window.set_system_cursor("crosshair")
            if t_type == "transect_marker":
                self.tool = MultiMarker(home=self.home, m_width=self.default_marker_width, b_height=self.btn_height)
            elif t_type == "transect_chain":
                self.tool = MultiChain(home=self.home, b_height=self.btn_height)
            self.add_widget(self.tool)
            self.home.populate_dynamic_sidebar(self.tool_action_widgets, "Actions")
            self.t_mode = True

    def add_to_sidebar(self, elements):
        """
        Adds elements to the dynamic sidebar.

        Args:
            elements (list): List of kivy.uix.Widgets to add to sidebar
        """
        self.tool_action_widgets = self.tool_action_widgets + elements
        self.home.populate_dynamic_sidebar(self.tool_action_widgets, "Actions")

    def remove_from_tool_action_widgets(self, element):
        """
        Removes element from widgets in 'Actions' sidebar menu.

        Args:
            element: kivy.uix.Widget to remove
        """
        self.tool_action_widgets.remove(element)
        if not self.editing and not self.dragging:
            self.home.populate_dynamic_sidebar(self.tool_action_widgets, "Actions")

    def close_tool(self, *args):
        """
        Closes tool and resets sidebar elements to non tool state.

        Args:
            args: Unused arguments passed to the method
        """
        if self.t_mode:
            kivy.core.window.Window.set_system_cursor("arrow")
            self.remove_widget(self.tool)
            self.tool_action_widgets = self.action_widgets
            self.home.populate_dynamic_sidebar(self.initial_side_bar, "Tools")
            self.t_mode = False

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
            self.home.populate_dynamic_sidebar(self.tool_action_widgets, "Actions")
            self.editing = False
        else:
            self.home.populate_dynamic_sidebar(self.edit_widgets, "Edit Mode")
            self.editing = True
        self.tool.change_dragging(self.editing)

    def drag_mode(self, *args):
        """
        Calls for transecting tool to turn dragging mode on if off and off if on

        Args:
            *args: Unused arguments passed to method when called.
        """
        if not self.dragging:
            self.home.populate_dynamic_sidebar([self.tran_mode_btn], "Drag Mode")
            kivy.core.window.Window.set_system_cursor("arrow")
            self.tool.change_dragging(True)
            self.dragging = True
        else:
            self.home.populate_dynamic_sidebar(self.tool_action_widgets, "Actions")
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
                self.contrast = func.contrast_function(value)
                self.update_netcdf()
        elif setting == "colormap":
            if self.f_type == "netcdf":
                self.colormap = value
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
        self.byte.seek(0)
        self.im = CoreImage(self.byte, ext='png')
        self.size = self.im.size
        self.img.texture = self.im.texture
        self.img.reload()

    def netcdf_to_image(self):
        """
        Creates image from NetCDF dataset defined in :attr:`nccut.filedisplay.FileDisplay.f_config`

        Normalizes data and then applies colormap and contrast settings and then calls for the creation of colorbar.
        Loads image into memory as io.BytesIO object so kivy can make image out of an array.
        """
        self.nc_data = np.flip(func.sel_data(self.config['netcdf']).data, 0)
        with warnings.catch_warnings(record=True) as w:
            n_data = (self.nc_data - np.nanmin(self.nc_data)) / (np.nanmax(self.nc_data) - np.nanmin(self.nc_data))
            if len(w) > 0 and issubclass(w[-1].category, RuntimeWarning):
                func.alert_popup("Selected data is all NaN")
        nans = np.repeat(np.isnan(n_data)[:, :, np.newaxis], 4, axis=2)
        c_mapped = plt.get_cmap(self.colormap)(n_data)
        whites = np.ones(c_mapped.shape)
        self.home.load_colorbar_and_info(func.get_color_bar(self.colormap, self.nc_data, (0.1, 0.1, 0.1), "white",
                                                            self.home.font * 2.5), self.config[self.f_type])
        img = np.where(nans, whites, c_mapped)
        # Applies contrast settings
        pil_image = im.fromarray(np.uint8(img * 255))
        img = ImageEnhance.Contrast(pil_image).enhance(self.contrast)
        self.byte = io.BytesIO()
        img.save(self.byte, format="PNG")

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
