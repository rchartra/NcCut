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
from kivy.graphics import Color, Line
from kivy.graphics.transformation import Matrix
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.scatterlayout import ScatterLayout
from kivy.core.window import Window
import kivy.uix as ui
from kivy.uix.label import Label
from kivy.core.image import Image as CoreImage
from kivy.metrics import dp
from PIL import Image as im
from PIL import ImageEnhance
import platform
import subprocess
from plyer import filechooser
import numpy as np
from scipy.interpolate import RegularGridInterpolator
import matplotlib.pyplot as plt
import io
import os
import pathlib
import re
import copy
import warnings
import nccut.functions as func
from nccut.multiorthogonalchain import MultiOrthogonalChain
from nccut.multiinlinechain import MultiInlineChain


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
        default_orthogonal_width: Default width for the orthogonal transect tool
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
        axis_font (float): Font to use for the plot axes. Not adjustable.
        x_pix (float) X coordinate units represented by one pixel
        y_pix (float): Y coordinate units represented by one pixel
        x_labels (list): List of x axis tick labels
        y_labels (list): List of y axis tick labels
        h_flip (bool): Has the data been flipped horizontally
        v_flip (bool): Has the data been flipped vertically
        contrast (int): Int from -127 to 127, contrast value to use when making image from NetCDF file
        l_col (str): Line color for transect tools: 'Blue', 'Green' or 'Orange'
        cir_size (float): Circle size for transect tools
        cmaps (dict): Dictionary of colormap names mapping to colormap values from cv2
        colormap: current colormap data
        btn_height: Height for buttons in sidebar which adapts to font size
        tools_lbl: "Tools" sidebar label
        inline_chain_btn: Inline chain button which opens inline chain tool
        orthogonal_chain_btn: Orthogonal chain button which opens orthogonal chain tool
        initial_side_bar (list): List of sidebar buttons in 'Transect Tools' sidebar menu
        tool_actions_lbl: "Tool Actions" sidebar label
        new_chain_btn: New Chain button to be loaded when in transect mode
        drag_btn: Drag button to be loaded when in transect mode
        edit_btn: Edit button to be loaded when in transect mode
        close_tool_btn: Button to close currently loaded tool
        chain_data_lbl: "Chain Data" sidebar label
        open_data_btn: Button to open previously exported chain data
        tool_sb_widgets_constant: Initial list of widgets in main tool meny menu, not including any widgets added by the
            tool
        tool_sb_widgets: List of widgets in main tool menu at any given moment
        drag_mode_lbl: "Drag Mode" sidebar label
        tran_mode_btn: Button to close Drag Mode
        edit_mode_lbl: "Edit Mode" sidebar label
        back_btn: Back button for editing mode
        delete_chain_btn: Delete chain button
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
            t_config (dict): Dictionary holding tool configurations: default orthogonal width
        """
        super(FileDisplay, self).__init__(**kwargs)

        self.config = f_config
        self.default_orthogonal_width = t_config["orthogonal_width"]
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

        # Axes info
        self.axis_font = dp(14)
        self.x_pix = 1
        self.y_pix = 1

        self.x_labels = []
        self.y_labels = []
        self.h_flip = False
        self.v_flip = False

        self.contrast = func.contrast_function(g_config["contrast"])
        self.l_col = g_config["line_color"]
        self.cir_size = g_config["circle_size"]

        self.cmaps = plt.colormaps()[:87]
        self.colormap = g_config["colormap"]
        self.btn_height = dp(20) + self.home.font
        # Initial Sidebar Widgets
        self.tools_lbl = func.SidebarHeaderLabel(text="Tools")
        self.inline_chain_btn = func.RoundedButton(text="Inline Chain", size_hint_y=None, height=self.btn_height,
                                                   font_size=self.home.font)
        self.inline_chain_btn.bind(on_press=lambda x: self.tool_btn("inline_chain"))

        self.orthogonal_chain_btn = func.RoundedButton(text="Orthogonal Chain", size_hint_y=None, height=self.btn_height,
                                                       font_size=self.home.font)
        self.orthogonal_chain_btn.bind(on_press=lambda x: self.tool_btn("orthogonal_chain"))
        self.initial_side_bar = [self.tools_lbl, self.inline_chain_btn, self.orthogonal_chain_btn]

        # Tool Action Widgets
        self.tool_actions_lbl = func.SidebarHeaderLabel(text="Tool Actions")

        self.new_chain_btn = func.RoundedButton(text="New Chain", size_hint_y=None, height=self.btn_height,
                                                halign='center', valign='center', font_size=self.home.font)
        self.new_chain_btn.bind(on_press=lambda x: self.tool.new_chain())

        self.drag_btn = func.RoundedButton(text="Drag Mode", size_hint_y=None, height=self.btn_height,
                                           halign='center', valign='center', font_size=self.home.font)
        self.drag_btn.bind(on_press=self.drag_mode)
        self.edit_btn = func.RoundedButton(text="Edit Mode", size_hint_y=None, height=self.btn_height,
                                           halign='center', valign='center', font_size=self.home.font)
        self.edit_btn.bind(on_press=self.edit_mode)
        self.close_tool_btn = func.RoundedButton(text="Close Tool", size_hint_y=None, height=self.btn_height,
                                                 halign='center', valign='center', font_size=self.home.font)
        self.close_tool_btn.bind(on_press=self.close_tool)

        # Chain Data Widgets
        self.chain_data_lbl = func.SidebarHeaderLabel(text="Chain Data")
        self.open_data_btn = func.RoundedButton(text="Open Data", size_hint_y=None, height=self.btn_height,
                                                halign='center', valign='center', font_size=self.home.font)
        self.open_data_btn.bind(on_press=lambda x: self.open_data_pop())

        self.tool_sb_widgets_constant = [self.tool_actions_lbl, self.close_tool_btn, self.drag_btn, self.edit_btn,
                                         self.new_chain_btn, self.chain_data_lbl, self.open_data_btn]
        self.tool_sb_widgets = copy.copy(self.tool_sb_widgets_constant)

        # Drag Mode Widgets
        self.drag_mode_lbl = func.SidebarHeaderLabel(text="Drag Mode")
        self.tran_mode_btn = func.RoundedButton(text="Transect Mode", size_hint_y=None, height=self.btn_height,
                                                halign='center', valign='center', font_size=self.home.font)
        self.tran_mode_btn.bind(on_press=self.drag_mode)
        self.drag_mode_widgets = [self.drag_mode_lbl, self.tran_mode_btn]

        # Editing Mode widgets
        self.edit_mode_lbl = func.SidebarHeaderLabel(text="Edit Mode")
        self.back_btn = func.RoundedButton(text="Back", size_hint_y=None, height=self.btn_height,
                                           halign='center', valign='center', font_size=self.home.font)
        self.back_btn.bind(on_press=self.edit_mode)
        self.delete_chain_btn = func.RoundedButton(text="Delete Last Chain", size_hint_y=None, height=self.btn_height,
                                                   font_size=self.home.font)
        self.delete_chain_btn.bind(on_press=lambda x: self.tool.del_chain())
        self.delete_point_btn = func.RoundedButton(text="Delete Last Point", size_hint_y=None, height=self.btn_height,
                                                   font_size=self.home.font)
        self.delete_point_btn.bind(on_press=lambda x: self.tool.del_point())

        self.edit_widgets = [self.edit_mode_lbl, self.back_btn, self.delete_chain_btn, self.delete_point_btn]

        self.load_image()
        Window.bind(on_key_down=self.on_key)

    # Turn off ScatterLayout functionality that conflicts with functionality
    ScatterLayout.do_rotation = False
    ScatterLayout.do_scale = False

    def on_key(self, *args):
        """
        If escape key is pressed, tool is loaded, and plot menu is not open then delete chain

        Args:
            args: Index 1 is key ascii code
        """
        key_ascii = args[1]
        if key_ascii == 27 and self.tool and not self.home.plot_popup.is_open:
            self.tool.del_chain()

    def font_adapt(self, font):
        """
        Update editing mode button and color bar font sizes.

        Args:
            font (float): New font size
        """
        self.back_btn.font_size = font
        self.delete_chain_btn.font_size = font
        self.delete_point_btn.font_size = font
        # Re-centers and rescales image on viewer resize
        self.x_axis()
        self.y_axis()
        if self.f_type == "netcdf":
            self.home.update_colorbar(func.get_color_bar(self.colormap, self.nc_data, (0.1, 0.1, 0.1),
                                                         "white", font * 2.5))
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
        self.home.populate_dynamic_sidebar(self.initial_side_bar)
        # Necessary for when viewer doesn't change size on file load (image -> image)
        self.resize_to_fit()
        self.home.font_adapt()

    def resize_to_fit(self, *args):
        """
        Resizes image to be just large enough to fill viewer screen. Method is bound to size property.

        Args:
            args: Two element list of object and it's size
        """

        bounds = self.home.ids.view.size
        r = min([bounds[i] / self.bbox[1][i] for i in range(len(bounds))])
        self.apply_transform(Matrix().scale(r, r, r))
        xco = bounds[0] / 2 - self.bbox[1][0] / 2
        self.pos = (xco, 0)
        self.x_axis()
        self.y_axis()

    def open_data_pop(self):
        """
        Opens native operating system file browser to allow user to select previously exported file
        """
        try:
            if platform.system() == "Darwin":
                # Construct the AppleScript command for selecting json files
                script = """
                        set file_path to choose file of type {"public.json"}
                        POSIX path of file_path
                        """
                result = subprocess.run(
                    ['osascript', '-e', script],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
                if result.returncode == 0:
                    file_path = result.stdout.strip()
                    self.tool.check_file(file_path)
            else:
                path = filechooser.open_file(filters=["*.json"])
                if path is not None and len(path) != 0:
                    self.tool.check_file(path[0])
        except Exception:
            # If native file browser not working, provide manual file entry method
            content = ui.boxlayout.BoxLayout(orientation='horizontal')
            popup = Popup(title="File Name", content=content, size_hint=(0.5, 0.15))
            txt = TextInput(size_hint=(0.7, 1), hint_text="Enter Chain Data File Name")
            content.add_widget(txt)
            go = Button(text="Ok", size_hint=(0.1, 1))
            go.bind(on_press=lambda x: self.manual_check_file(txt.text))
            go.bind(on_release=popup.dismiss)
            close = Button(text="Close", size_hint=(0.2, 1), font_size=self.home.font)
            close.bind(on_press=popup.dismiss)
            content.add_widget(go)
            content.add_widget(close)
            popup.open()
            return

    def manual_check_file(self, text):
        """
        When native file browser is not working, checks manually entered text is a valid file path.

        Args:
            text: User entered file path
        """
        path = self.home.rel_path
        if text.find(".") >= 1:
            text = text[:text.find(".")]
        if text == "" or len(re.findall(r'[^A-Za-z0-9_\-/:\\]', text)) > 0:
            func.alert_popup("Invalid file name")
            return False
        if "/" in text:
            if not pathlib.Path.exists(path / text[:text.rfind("/") + 1]):
                func.alert_popup("Directory not found")
                return False
        if pathlib.Path.exists(path / (text + ".json")):
            fpath = os.path.abspath(text + ".json")
            self.tool.check_file(fpath)
        else:
            func.alert_popup("File not Found")

    def tool_btn(self, t_type):
        """
        Manages the creation and deletion of each tool.

        If a tool is currently loaded, remove it, switch cursor to an arrow
        and clean up. If not, load indicated tool and switches cursor to a cross.

        Args:
            t_type (str): Tool type: 'inline_chain' or 'orthogonal_chain'
        """

        if not self.t_mode:
            # Opens a new tool
            kivy.core.window.Window.set_system_cursor("crosshair")
            if t_type == "orthogonal_chain":
                self.tool = MultiOrthogonalChain(home=self.home, t_width=self.default_orthogonal_width,
                                                 b_height=self.btn_height)
            elif t_type == "inline_chain":
                self.tool = MultiInlineChain(home=self.home, b_height=self.btn_height)
            self.add_widget(self.tool)
            self.home.populate_dynamic_sidebar(self.tool_sb_widgets)
            self.t_mode = True

    def add_to_sidebar(self, element, index=-1):
        """
        Adds elements to the dynamic sidebar.

        Args:
            element: List of kivy.uix.Widget to add to sidebar
            index (int): Index in which to insert elements. Default is -1 which adds it to bottom of sidebar.
        """
        self.tool_sb_widgets.insert(index, element)
        self.home.populate_dynamic_sidebar(self.tool_sb_widgets)

    def remove_from_tool_sb_widgets(self, element):
        """
        Removes element from widgets in main tool sidebar menu.

        Args:
            element: kivy.uix.Widget to remove
        """
        self.tool_sb_widgets.remove(element)
        if not self.editing and not self.dragging:
            self.home.populate_dynamic_sidebar(self.tool_sb_widgets)

    def close_tool(self, *args):
        """
        Closes tool and resets sidebar elements to non tool state.

        Args:
            args: Unused arguments passed to the method
        """
        if self.t_mode:
            kivy.core.window.Window.set_system_cursor("arrow")
            self.remove_widget(self.tool)
            self.tool_sb_widgets = copy.copy(self.tool_sb_widgets_constant)
            self.home.populate_dynamic_sidebar(self.initial_side_bar)
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
            self.home.populate_dynamic_sidebar(self.tool_sb_widgets)
            self.editing = False
        else:
            self.home.populate_dynamic_sidebar(self.edit_widgets)
            self.editing = True
        self.tool.change_dragging(self.editing)

    def drag_mode(self, *args):
        """
        Calls for transecting tool to turn dragging mode on if off and off if on

        Args:
            *args: Unused arguments passed to method when called.
        """
        if not self.dragging:
            self.home.populate_dynamic_sidebar(self.drag_mode_widgets)
            kivy.core.window.Window.set_system_cursor("arrow")
            self.tool.change_dragging(True)
            self.dragging = True
        else:
            self.home.populate_dynamic_sidebar(self.tool_sb_widgets)
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
        # Select data
        config = self.config["netcdf"]
        if config['z'] == 'N/A':
            # 2D NetCDF data
            ds = config['data'][config['var']].rename({config['y']: 'y', config['x']: 'x'})
            data = ds.sel(y=ds['y'], x=ds['x'])
        else:
            # 3D NetCDF data
            ds = config['data'][config['var']].rename({config['y']: 'y', config['x']: 'x', config['z']: 'z'})
            ds['z'] = ds['z'].astype(str)
            data = ds.sel(y=ds['y'], x=ds['x'], z=config['z_val'])
        x_coord = ds['x'].data
        y_coord = ds['y'].data
        data = data.transpose('y', 'x')

        # Interpolate dataset dimensions to coordinate data
        interp = RegularGridInterpolator((y_coord, x_coord), data.data, method="linear", bounds_error=False,
                                         fill_value=None)
        self.x_pix = min(abs(x_coord[:-1] - x_coord[1:]))
        self.y_pix = min(abs(y_coord[:-1] - y_coord[1:]))
        x = np.arange(x_coord.min(), x_coord.max() + self.x_pix, self.x_pix)
        y = np.arange(y_coord.min(), y_coord.max() + self.y_pix, self.y_pix)
        xg, yg = np.meshgrid(x, y)
        self.nc_data = np.flip(interp((yg, xg)), 0)

        # Turn into image
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

    def x_axis(self):
        """
        Chooses x-axis tick distributions, calculates their locations, and draws them.
        """
        # Determine x coordinate data
        if self.f_type == "image":
            x_bounds = np.array([0, self.size[0]])
            x_name = "x"
        else:
            try:
                x_coord = self.config["netcdf"]["data"][self.config["netcdf"]["x"]].data.astype(float)
                x_bounds = np.array([x_coord.min(), x_coord.max() + self.x_pix])
            except ValueError:
                x_bounds = np.array([0, self.size[0]])
            x_attrs = self.config["netcdf"]["data"][self.config["netcdf"]["x"]].attrs
            if "long_name" in list(x_attrs.keys()):
                x_name = x_attrs["long_name"].title()
            else:
                x_name = self.config["netcdf"]["x"].title()
            if "units" in list(x_attrs.keys()):
                x_name = x_name + " (" + x_attrs["units"] + ")"

        x_range = x_bounds[1] - x_bounds[0]
        x_pos = self.bbox[0][0]
        width = self.bbox[1][0]
        plot_box = self.home.ids.plot_box
        h_flip = self.h_flip
        # Margin on edges to make sure text doesn't overflow
        m_right = dp(30)
        m_left = dp(10)
        cpp = x_range / width

        # Clean up old axis
        if len(self.x_labels) > 0:
            plot_box.canvas.remove_group("x_ticks")

        # Determine visible data range
        vis_x = np.array([0, width])
        if x_pos < m_left:
            vis_x[0] = -(x_pos - m_left)
        if x_pos + width > plot_box.width - m_right:
            vis_x[1] = vis_x[1] - (x_pos + width - (plot_box.width - m_right))
        vis_factors = vis_x / width
        if h_flip:
            dat_range = x_bounds[1] - (x_range * vis_factors)
        else:
            dat_range = x_bounds[0] + (x_range * vis_factors)
        # Determine goal tick density (not necessarily the actual density)
        vis_width = np.diff(width * vis_factors)[0]
        d = vis_width / 70
        if d < 2:
            d = 2
        elif d > 9:
            d = 9
        # Select and format labels
        if h_flip:
            dat_range = np.flip(dat_range)
        if dat_range[0] >= dat_range[1]:
            selected_labels = [dat_range[0]]
        else:
            selected_labels = func.label_placer(dat_range[0], dat_range[1], d)
            selected_labels = selected_labels[np.where((selected_labels >= dat_range[0]) & (selected_labels <= dat_range[1]))]
        if len(selected_labels) < 2:
            selected_labels = [dat_range[0], dat_range[1]]
        rep = "{:.2e}".format(selected_labels[0])
        exp_str = rep[rep.find("e"):]
        exp = int(exp_str[1:])
        if abs(exp) > 2:
            formatted_labels = [round(elem / 10 ** exp, 2) for elem in selected_labels]
            exp_str = " (" + exp_str + ")"
        else:
            formatted_labels = [round(elem, 2) for elem in selected_labels]
            exp_str = ""
        formatted_labels = [int(lab) if lab.is_integer() else lab for lab in formatted_labels]
        if h_flip:
            formatted_labels = np.flip(formatted_labels)
            selected_labels = np.flip(selected_labels)
        # Determine tick positions
        if h_flip:
            label_pos = [(width - (x - x_bounds[0]) / cpp) + x_pos for x in selected_labels]
        else:
            label_pos = [(x - x_bounds[0]) / cpp + x_pos for x in selected_labels]
        # Draw ticks
        tick_top = 0
        tick_bottom = -dp(5)

        with plot_box.canvas:
            Color(1, 1, 1)
            if x_pos > 0:
                Line(points=[x_pos, tick_top, x_pos, tick_bottom - dp(3)], width=dp(1), cap="none", group="x_ticks")
            for p in label_pos:
                Line(points=[p, tick_top, p, tick_bottom], width=dp(1), cap="none", group="x_ticks")
            if x_pos + width < plot_box.width:
                Line(points=[x_pos + width, tick_top, x_pos + width, tick_bottom - dp(3)], width=dp(1), cap="none", group="x_ticks")

        # Add or remove labels until have required amount
        while len(self.x_labels) < len(formatted_labels):
            lab = Label(text="", color=[1, 1, 1, 1], halign="left", size_hint=(None, None),
                        font_size=self.axis_font)
            lab.bind(texture_size=lab.setter("size"))
            self.x_labels.append(lab)
            plot_box.add_widget(lab)
        while len(self.x_labels) > len(formatted_labels):
            plot_box.remove_widget(self.x_labels.pop(0))

        # Place tick labels
        for i, x in enumerate(formatted_labels):
            lab = self.x_labels[i]
            lab.text = str(x)
            lab.pos = (float(label_pos[i]) - self.axis_font / 2, tick_top - self.axis_font * 1.6)

        # Update x label
        self.home.ids.x_axis_label.text = x_name + exp_str

    def y_axis(self):
        """
        Chooses y-axis tick distributions, calculates their locations, and draws them.
        """
        # Determine x coordinate data
        if self.f_type == "image":
            y_bounds = np.array([0, self.size[1]])
            y_name = "y"
        else:
            try:
                y_coord = self.config["netcdf"]["data"][self.config["netcdf"]["y"]].data.astype(float)
                y_bounds = np.array([y_coord.min(), y_coord.max() + self.y_pix])
            except ValueError:
                y_bounds = np.array([0, self.size[1]])
            y_attrs = self.config["netcdf"]["data"][self.config["netcdf"]["y"]].attrs
            if "long_name" in list(y_attrs.keys()):
                y_name = y_attrs["long_name"].title()
            else:
                y_name = self.config["netcdf"]["y"].title()
            if "units" in list(y_attrs.keys()):
                y_name = y_name + " (" + y_attrs["units"] + ")"

        y_range = y_bounds[1] - y_bounds[0]
        y_pos = self.bbox[0][1]
        height = self.bbox[1][1]
        m_top = dp(10)
        plot_box = self.home.ids.plot_box
        v_flip = self.v_flip
        cpp = y_range / height

        # Clean up old axis
        if len(self.y_labels) > 0:
            plot_box.canvas.remove_group("y_ticks")

        # Determine visible data range
        vis_y = np.array([0, height])
        if y_pos < 0:
            vis_y[0] = -y_pos
        if y_pos + height > plot_box.height - m_top:
            vis_y[1] = vis_y[1] - (y_pos + height - (plot_box.height - m_top))
        vis_factors = vis_y / height
        if v_flip:
            dat_range = y_bounds[1] - (y_range * vis_factors)
        else:
            dat_range = y_bounds[0] + (y_range * vis_factors)
        # Determine goal tick density (not necessarily the actual density)
        vis_height = np.diff(height * vis_factors)[0]
        d = vis_height / 70
        if d < 2:
            d = 2
        elif d > 9:
            d = 9
        # Select and format labels
        if v_flip:
            dat_range = np.flip(dat_range)
        if dat_range[0] >= dat_range[1]:
            selected_labels = [dat_range[0]]
        else:
            selected_labels = func.label_placer(dat_range[0], dat_range[1], d)
            selected_labels = selected_labels[
                np.where((selected_labels >= dat_range[0]) & (selected_labels <= dat_range[1]))]
        if len(selected_labels) < 2:
            selected_labels = [dat_range[0], dat_range[1]]
        rep = "{:.2e}".format(selected_labels[-1])
        exp_str = rep[rep.find("e"):]
        exp = int(exp_str[1:])
        if abs(exp) > 2:
            formatted_labels = [round(elem / 10 ** exp, 2) for elem in selected_labels]
            exp_str = " (" + exp_str + ")"
        else:
            formatted_labels = [round(elem, 2) for elem in selected_labels]
            exp_str = ""
        formatted_labels = [int(lab) if lab.is_integer() else lab for lab in formatted_labels]
        if v_flip:
            formatted_labels = np.flip(formatted_labels)
            selected_labels = np.flip(selected_labels)
        # Determine tick positions
        if v_flip:
            label_pos = [(height - (y - y_bounds[0]) / cpp) + y_pos for y in selected_labels]
        else:
            label_pos = [(y - y_bounds[0]) / cpp + y_pos for y in selected_labels]
        # Draw ticks
        tick_right = 0
        tick_left = -dp(5)

        with plot_box.canvas:
            Color(1, 1, 1)
            if y_pos > 0:
                Line(points=[tick_left - dp(3), y_pos, tick_right, y_pos], width=dp(1), cap="none", group="y_ticks")
            for p in label_pos:
                Line(points=[tick_left, p, tick_right, p], width=dp(1), cap="none", group="y_ticks")
            if y_pos + height < plot_box.height:
                Line(points=[tick_left - dp(3), y_pos + height, tick_right, y_pos + height], width=dp(1), cap="none",
                     group="y_ticks")

        # Add or remove labels until have required amount
        while len(self.y_labels) < len(formatted_labels):
            lab = Label(text="", color=[1, 1, 1, 1], halign="left", size_hint=(None, None),
                        font_size=self.axis_font)
            lab.bind(texture_size=lab.setter("size"))
            self.y_labels.append(lab)
            plot_box.add_widget(lab)
        while len(self.y_labels) > len(formatted_labels):
            plot_box.remove_widget(self.y_labels.pop(0))

        # Place tick labels
        for i, y in enumerate(formatted_labels):
            lab = self.y_labels[i]
            lab.text = str(y)
            lab.pos = (tick_left - self.axis_font * 2, float(label_pos[i]) - self.axis_font / 2)

        # Update y label
        self.home.ids.y_axis_label.text = y_name + exp_str

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
        self.v_flip = not self.v_flip
        self.y_axis()

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
        self.h_flip = not self.h_flip
        self.x_axis()

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
                    if self.scale < 30:
                        mat = Matrix().scale(1.1, 1.1, 1.1)
                        self.apply_transform(mat, anchor=touch.pos)
                elif touch.button == 'scrollup':
                    if self.scale > 0.1:
                        mat = Matrix().scale(.9, .9, .9)
                        self.apply_transform(mat, anchor=touch.pos)
            else:
                super(FileDisplay, self).on_touch_down(touch)
            self.x_axis()
            self.y_axis()

    def on_touch_move(self, touch):
        """
        Calls for axes to update when plot is moved.

        Args:
            touch: MouseMotionEvent, see kivy docs for details
        """
        super(FileDisplay, self).on_touch_move(touch)
        self.x_axis()
        self.y_axis()
