"""
UI and functionality for NetCDF configuration popup

Creates the NetCDF configuration popup that opens when a user loads a NetCDF file. Ensures that the file
is in a viable configuration for the viewer.
"""

import kivy.uix as ui
from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.dropdown import DropDown
import cutview.functions as func
import xarray as xr


class NetCDFConfig(Popup):
    """
    UI and functionality for NetCDF configuration popup

    Creates the NetCDF configuration popup that opens when a user loads a NetCDF file. Ensures that the file
    is in a viable configuration for the viewer.

    Attributes:
        home: Reference to root :class:`cutview.homescreen.HomeScreen` instance
        data: xarray.Dataset, Opened NetCDF file
        var_select: RoundedButton, Variable select button
        var_drop: Dropdown(), Dropdown of variable options
        x_select: Rounded Button, X dimension select button
        y_select: Rounded Button, Y dimension select button
        z_select: Rounded Button, Z dimension select button
        depth_select: Rounded Button, Z dimension value select button
        error: Label for displaying error alerts
        title: Popup title
        content: BoxLayout containing all widgets of the popup
        size_hint (tuple): Tuple (width, height) of relative size of popup to window

        Inherits additional attributes from kivy.uix.popup.Popup (see kivy docs)
    """
    def __init__(self, file, home, **kwargs):
        """
        Defines UI elements and opens popup.

        Args:
            file (str): File path of NetCDF file. Must exist and be a valid NetCDF file
            home: Reference to root :class:`cutview.homescreen.HomeScreen` instance
        """
        super(NetCDFConfig, self).__init__(**kwargs)
        self.home = home
        self.data = xr.open_dataset(file)
        content = ui.boxlayout.BoxLayout(orientation='vertical', spacing=dp(20), padding=dp(20))

        # Variable Selection
        var_box = ui.boxlayout.BoxLayout(spacing=dp(20))
        var_box.add_widget(Label(text="Variable: ", size_hint=(0.3, 1)))
        self.var_select = func.RoundedButton(text="Select...", size_hint=(0.7, 1))
        self.var_drop = DropDown()
        for item in list(self.data.keys()):
            btn = Button(text=str(item), size_hint_y=None, height=30)
            btn.bind(on_release=lambda btn: self.var_drop.select(btn.text))
            btn.bind(on_press=self.var_drop.dismiss)
            self.var_drop.add_widget(btn)
        self.var_drop.bind(on_select=lambda instance, x: self.var_update(x))
        self.var_select.bind(on_release=self.var_drop.open)
        var_box.add_widget(self.var_select)
        content.add_widget(var_box)

        # X, Y Selection
        xy_box = ui.boxlayout.BoxLayout(spacing=dp(20))
        xy_box.add_widget(Label(text="X: ", size_hint=(0.2, 1)))
        self.x_select = func.RoundedButton(text="Select...", size_hint=(0.3, 1))
        self.x_select.bind(on_release=lambda x: self.dim_options(self.x_select))
        xy_box.add_widget(self.x_select)

        xy_box.add_widget(Label(text="Y: ", size_hint=(0.2, 1)))
        self.y_select = func.RoundedButton(text="Select...", size_hint=(0.3, 1))
        self.y_select.bind(on_release=lambda x: self.dim_options(self.y_select))
        xy_box.add_widget(self.y_select)
        content.add_widget(xy_box)

        # Z selection (not always required)
        z_box = ui.boxlayout.BoxLayout(spacing=dp(20))
        z_box.add_widget(Label(text="Z Variable: ", size_hint=(0.2, 1)))
        self.z_select = func.RoundedButton(text="Select...", size_hint=(0.3, 1))
        self.z_select.bind(on_release=lambda x: self.dim_options(self.z_select))
        z_box.add_widget(self.z_select)

        z_box.add_widget(Label(text="Z Value: ", size_hint=(0.2, 1)))
        self.depth_select = func.RoundedButton(text="Select...", size_hint=(0.3, 1))
        z_box.add_widget(self.depth_select)
        self.depth_select.bind(on_release=self.depth_options)
        content.add_widget(z_box)

        # Popup Controls
        c_box = ui.boxlayout.BoxLayout(spacing=dp(20))
        self.error = Label(text="", size_hint=(0.7, 1))
        c_box.add_widget(self.error)
        back = func.RoundedButton(text="Back", size_hint=(0.15, 1))
        back.bind(on_press=self.dismiss)
        c_box.add_widget(back)
        self.go = func.RoundedButton(text="Go", size_hint=(0.15, 1))
        self.go.bind(on_press=self.check_inputs)
        c_box.add_widget(self.go)
        content.add_widget(c_box)

        # Final settings
        self.title = "NetCDF Configuration"
        self.content = content
        self.size_hint = (0.8, 0.8)
        self.bind(on_dismiss=lambda x: self.clean())
        self.open()

    def clean(self):
        """
        Resets file related attributes of the root :class:`cutview.homescreen.HomeScreen` instance
        """
        if not self.home.file_on:
            self.home.clean_file()

    def check_inputs(self, *args):
        """
        Check selected configurations are valid before loading dataset

        When values are selected the button text changes to the selection. This method
        accesses values from the text of the buttons. If all checks are passed sends
        dictionary of configurations to HomeScreen instance and closes popup. Otherwise
        an error message is displayed and popup stays open.
        """
        vals = {'x': self.x_select.text, 'y': self.y_select.text,
                'z': self.z_select.text, 'z_val': self.depth_select.text,
                'var': self.var_select.text, 'file': self.data}
        selects = [(self.x_select, "X Dimension"), (self.y_select, "Y Dimension")]
        if self.var_select.text == "Select...":
            self.error.text = "Please Select a Variable"
            return
        if len(self.data[self.var_select.text].dims) > 3:
            self.error.text = "This variable has more than 3 dimensions"
            return
        if len(self.data[self.var_select.text].dims) < 2:
            self.error.text = "This variable has less than 2 dimensions"
            return
        for sel in selects:
            if sel[0].text == 'Select...':
                self.error.text = "Please Select a " + sel[1]
                return
        if len(set(list(vals.values())[:-3])) != len(list(vals.values())[:-3]):
            self.error.text = "All X, Y, Z variables must be unique"
            return
        if len(self.data[self.var_select.text].dims) == 3:
            if self.z_select.text == "Select...":
                self.error.text = "Please Select a Z dimension"
                return
            if self.depth_select.text == 'Select...':
                self.error.text = "Please Select a Z Value"
                return
        self.home.load_netcdf(vals)
        self.dismiss()

    def var_update(self, var, *args):
        """
        When a variable is selected updates var_select button text to the variable name. Then finds first
        two or three dimensions of the variable and sets them as the X, Y, and Z (if three) dimension
        selections.

        Args:
            var (str): Variable selected
            *args: Unused arguments passed to method
        """
        setattr(self.var_select, 'text', var)
        dims = list(self.data[self.var_select.text].dims)
        if len(dims) < 3:
            while len(dims) < 3:
                dims.append("Select...")
        elif len(dims) > 3:
            dims = dims[:3]
        setattr(self.x_select, 'text', dims[0])
        setattr(self.y_select, 'text', dims[1])
        setattr(self.z_select, 'text', dims[2])
        setattr(self.depth_select, 'text', "Select...")

    def dim_options(self, dim, *args):
        """
        Creates dropdown for X, Y, or Z dimension selection button. If variable is already selected
        options listed are all dimensions for selected variable. If variable is not selected sets button
        to 'Select ...'

        Args:
            dim: x_select, y_select, or z_select Button
            *args: Unused arguments passed to method
        """
        if self.var_select.text != "Select...":
            dim_drop = ListDropDown(['Select...'] + list(self.data[self.var_select.text].dims), dim)
            dim_drop.open(dim)
        else:
            dim.text = "Select..."

    def depth_options(self, *args):
        """
        Creates dropdown for the value of Z dimension if third dimension is selected.

        Args:
            *args: Unused arguments passed to method
        """
        if self.z_select.text != "Select...":
            depth_drop = ListDropDown(['Select...'] + list(self.data.coords[self.z_select.text].data), self.depth_select)
            depth_drop.open(self.depth_select)
        else:
            self.depth_select.text = "Select..."


class ListDropDown(DropDown):
    """
    Standard dropdown for all selections in the menu.

    Attributes:
        Inherits attributes from kivy.uix.dropdown.Dropdown (see kivy docs)
    """
    def __init__(self, items, button, **kwargs):
        """
        Creates dropdown. When options in dropdown are selected dropdown closes and selection button
        text changes to the selected option.

        Args:
            items: List of items to be options for dropdown.
            button: Button which opens dropdown
        """
        super(ListDropDown, self).__init__(**kwargs)
        for item in items:
            btn = Button(text=str(item), size_hint_y=None, height=30)
            btn.bind(on_release=lambda btn: self.select(btn.text))
            btn.bind(on_press=self.dismiss)
            self.add_widget(btn)
        self.bind(on_select=lambda instance, x: setattr(button, 'text', x))
