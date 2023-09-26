import kivy.uix as ui
from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.dropdown import DropDown
import functions as func
import xarray as xr
import time


class NetCDFConfig(Popup):
    def __init__(self, file, home, **kwargs):
        super(NetCDFConfig, self).__init__(**kwargs)
        self.home = home
        self.data = xr.open_dataset(file)

        content = ui.boxlayout.BoxLayout(orientation='vertical', spacing=dp(20), padding=dp(20))

        # Variable Selection
        var_box = ui.boxlayout.BoxLayout(spacing=dp(20))
        var_box.add_widget(Label(text="Variable: ", size_hint=(0.3, 1)))
        self.var_select = func.RoundedButton(text="Select...", size_hint=(0.7, 1))
        self.var_drop = ListDropDown(list(self.data.keys()), self.var_select)
        self.var_select.bind(on_release=self.var_drop.open)
        var_box.add_widget(self.var_select)
        content.add_widget(var_box)

        # X, Y Selection
        xy_box = ui.boxlayout.BoxLayout(spacing=dp(20))
        xy_box.add_widget(Label(text="X: ", size_hint=(0.2, 1)))
        self.x_select = func.RoundedButton(text=list(self.data.dims)[0], size_hint=(0.3, 1))
        self.x_drop = ListDropDown(list(self.data.dims), self.x_select)
        self.x_select.bind(on_release=self.x_drop.open)
        xy_box.add_widget(self.x_select)

        xy_box.add_widget(Label(text="Y: ", size_hint=(0.2, 1)))
        self.y_select = func.RoundedButton(text=list(self.data.dims)[1], size_hint=(0.3, 1))
        self.y_drop = ListDropDown(list(self.data.dims), self.y_select)
        self.y_select.bind(on_release=self.y_drop.open)
        xy_box.add_widget(self.y_select)
        content.add_widget(xy_box)

        # Z selection (optional)
        z_box = ui.boxlayout.BoxLayout(spacing=dp(20))
        z_box.add_widget(Label(text="Z Variable: ", size_hint=(0.2, 1)))
        self.z_select = func.RoundedButton(text="Select...", size_hint=(0.3, 1))
        self.z_drop = ListDropDown(['Select...'] + list(self.data.dims), self.z_select)
        self.z_select.bind(on_release=self.z_drop.open)
        z_box.add_widget(self.z_select)

        z_box.add_widget(Label(text="Z Value: ", size_hint=(0.2, 1)))
        self.depth_select = func.RoundedButton(text="Select...", size_hint=(0.3, 1))
        z_box.add_widget(self.depth_select)
        self.depth_select.bind(on_release=self.depth_options)
        content.add_widget(z_box)

        # Controls
        c_box = ui.boxlayout.BoxLayout(spacing=dp(20))
        self.error = Label(text="", size_hint=(0.7, 1))
        c_box.add_widget(self.error)
        back = func.RoundedButton(text="Back", size_hint=(0.15, 1))
        back.bind(on_press=self.dismiss)
        c_box.add_widget(back)
        go = func.RoundedButton(text="Go", size_hint=(0.15, 1))
        go.bind(on_press=self.check_inputs)
        c_box.add_widget(go)
        content.add_widget(c_box)

        # Final settings
        self.title = "NetCDF Configuration"
        self.content = content
        self.size_hint = (0.8, 0.8)

        self.open()

    def check_inputs(self, *args):
        # Check configurations are valid before submitting
        vals = {'x': self.x_select.text, 'y': self.y_select.text,
                'z': self.z_select.text, 'z_val': self.depth_select.text,
                'var': self.var_select.text, 'file': self.data}
        if len(set(list(vals.values())[:-3])) != len(list(vals.values())[:-3]):
            self.error.text = "All X, Y, Z variables must be unique"
            return
        if self.var_select.text == 'Select...':
            self.error.text = "Please Select a Variable"
            return
        if self.z_select.text != "Select..." and self.z_select.text not in self.data[self.var_select.text].dims:
            self.error.text = "Z selection is not a dimension for this variable"
            return
        if self.z_select.text == "Select..." and len(self.data[self.var_select.text].dims) == 3:
            self.error.text = "This variable requires a Z value"
            return
        if len(self.data[self.var_select.text].dims) > 3:
            self.error.text = "This variable has more than 3 dimensions"
            return
        if self.z_select.text != 'Select...' and self.depth_select.text == 'Select...':
            self.error.text = "Please Select a Z Value"
            return
        t0 = time.time()
        self.home.nc_open(vals)
        t1 = time.time()
        print("nc_open(): " + str(t1-t0))
        self.dismiss()

    def depth_options(self, *args):
        # Z Value Dropdown
        if self.z_select.text != "Select...":
            depth_drop = ListDropDown(['Select...'] + list(self.data.coords[self.z_select.text].data), self.depth_select)
            depth_drop.open(self.depth_select)
        else:
            self.depth_select.text = "Select..."


class ListDropDown(DropDown):
    # Standard dropdown code
    def __init__(self, items, button, **kwargs):
        super(ListDropDown, self).__init__(**kwargs)
        for item in items:
            btn = Button(text=str(item), size_hint_y=None, height=30)
            btn.bind(on_release=lambda btn: self.select(btn.text))
            btn.bind(on_press= self.dismiss)
            self.add_widget(btn)
        self.bind(on_select=lambda instance, x: setattr(button, 'text', x))
