"""
Defines functionality for adding, removing, and adjusting the settings bar menu at the top of the screen.
The UI code is in nccut.kv and code for the individual dropdowns is in nccut.dropdowns.
"""


from kivy.uix.boxlayout import BoxLayout
import nccut.functions as func
import nccut.dropdowns as dd


class SettingsBar(BoxLayout):
    """
    Defines functionality for adding, removing, and adjusting the settings bar menu at the top of the screen.
    The UI code is in nccut.kv and code for the individual dropdowns is in nccut.dropdowns.

    Args:
        home: Reference to root HomeScreen instance
        font (float): Current font_size for all text containing elements
        f_m (float): Multiplier to use across all elements for font_size adjustment
        netcdf_btn: Reference to the button that opens the NetCDF settings menu.
    """
    def __init__(self, font, home, **kwargs):
        super(SettingsBar, self).__init__(**kwargs)
        """
        Creates button to open NetCDF menu

        Args:
            font: Initial font size to use
            home: Reference to root HomeScreen instance
        """
        self.home = home
        self.font = font
        self.f_m = 0.7
        self.netcdf_btn = func.RoundedButton(text="NetCDF", size_hint=(0.15, 1), font_size=self.font * self.f_m)
        self.netcdf_btn.bind(on_press=self.open_netcdf)

    def font_adapt(self, font):
        """
        Sets font of widgets with text to new font.

        Args:
            font: New font
        """
        self.netcdf_btn.font_size = font * self.f_m

    def open_netcdf(self, *args):
        """
        Opens NetCDF settings menu
        """
        dd.NetCDFDropDown().open(self.netcdf_btn)

    def add_netcdf_button(self):
        """
        Adds button to access NetCDF settings menu
        """
        if self.netcdf_btn.parent is None:
            self.add_widget(self.netcdf_btn, len(self.children))

    def remove_netcdf_button(self):
        """
        Removes button to access NetCDF settings menu
        """
        if self.netcdf_btn.parent is not None:
            self.remove_widget(self.netcdf_btn)

    def set_line_color_btn(self, btn_img_path):
        """
        Sets line color setting button image to image at specified path

        Args:
            btn_img_path (String): Path to button image
        """
        self.ids.line_color_btn_img.source = btn_img_path

    def rotate(self):
        """
        Call for a 45 degree rotation of current display by 45 degrees
        """
        if self.home.file_on:
            self.home.display.rotate()

    def v_flip(self):
        """
        Call for a vertical flip of view of current display
        """
        if self.home.file_on:
            self.home.display.flip_vertically()

    def h_flip(self):
        """
        Call for a horizontal flip of view of current display
        """
        if self.home.file_on:
            self.home.display.flip_horizontally()
