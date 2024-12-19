# SPDX-FileCopyrightText: 2024 University of Washington
#
# SPDX-License-Identifier: BSD-3-Clause

"""
Orthogonal chain width adjustment tool.

Popup that allows the control of width of orthogonal transects made via the
orthogonal chain tool. Ensures given width is within bounds of data.
"""

from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
import nccut.functions as func


class OrthogonalChainWidth(Popup):
    """
    Orthogonal Chain width adjustment tool.

    Popup that allows the control of width of orthogonal transects made via the
    orthogonal chain tool. Ensures given width is within bounds of data.

    Attributes:
        spacing: The spacing between widgets in the layout
        txt: kivy.uix.textinput.TextInput widget where user enters their desired width
        btn: 'Set' Button
        orthogonal_chain: Current :class:`nccut.multiorthogonalchain.MultiOrthogonalChain` instance
        min (int): Minimum width allowed
        max (int): Maximum width allowed
    """
    def __init__(self, orthogonal_chain, **kwargs):
        """
        Defines graphical elements.

        Args:
            orthogonal_chain: Active :class:`nccut.multiorthogonalchain.MultiOrthogonalChain` instance
        """
        super(OrthogonalChainWidth, self).__init__(**kwargs)
        self.font_size = orthogonal_chain.home.font
        self.title = "Set Orthogonal Transect Width"
        self.title_size = self.font_size
        content = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(12))
        display = orthogonal_chain.home.display

        # Description of unit coordinate
        x_units = ""
        y_units = ""
        if list(display.config.keys())[0] == "image":
            x_label = "pixel"
            y_label = "pixel"
        else:
            config = display.config["netcdf"]
            x_label = config["x"]
            y_label = config["y"]
            x_attrs = config["data"][x_label].attrs
            if "units" in list(x_attrs.keys()):
                x_units = "[b]" + x_attrs["units"] + "[/b] "

            y_attrs = config["data"][y_label].attrs
            if "units" in list(y_attrs.keys()):
                y_units = "[b]" + y_attrs["units"] + "[/b] "
        self.max = max(display.size)
        self.min = 3
        scroll = ScrollView(size_hint=(1, 0.6), do_scroll_x=False)
        description = "Enter the number of unit coordinates between [b]" + str(self.min) + "[/b] and [b]" + \
                      str(self.max) + "[/b]\n    \u2022 One unit coordinate is: \n        \u2022 [b]" + \
                      str(round(display.x_pix, 5)) + "[/b] " + x_units + "in the X dimension (" + x_label + \
                      ") \n        \u2022 [b]" + str(round(display.y_pix, 5)) + "[/b] " + y_units + \
                      "in the Y dimension (" + y_label + ") \n\n The current width is [b]" + \
                      str(orthogonal_chain.curr_width) + "[/b]"
        self.description = Label(text=description, font_size=self.font_size, size_hint_y=None, text_size=(None, None),
                                 halign="left", valign="top", markup=True)
        self.description.bind(
            width=lambda instance, value: setattr(instance, 'text_size', (value, None)),
            texture_size=lambda instance, value: setattr(instance, 'height', value[1])
        )
        scroll.add_widget(self.description)
        # Text Entry
        self.txt = TextInput(hint_text="Enter Transect Width", font_size=self.font_size, size_hint_y=0.2)

        # Buttons
        buttons = BoxLayout(size_hint_y=0.2, spacing=dp(10))

        self.set_btn = func.RoundedButton(text="Set", size_hint=(.15, 1), font_size=self.font_size)
        self.back_btn = func.RoundedButton(text="Back", size_hint=(.15, 1), font_size=self.font_size)

        self.set_btn.bind(on_press=lambda x: self.update())
        self.back_btn.bind(on_press=self.dismiss)
        self.error_msg = Label(text="", size_hint_x=0.7, markup=True)
        buttons.add_widget(self.error_msg)
        buttons.add_widget(self.back_btn)
        buttons.add_widget(self.set_btn)

        content.add_widget(scroll)
        content.add_widget(self.txt)
        content.add_widget(buttons)
        self.add_widget(content)

        self.orthogonal_chain = orthogonal_chain
        self.size_hint = (None, None)
        self.size = (dp(500), dp(300))
        self.open()

    def update(self):
        """
        Update width of current orthogonal chain if given a valid width.
        """
        num = self.txt.text
        if num.isnumeric():
            num = float(num)
            if self.min <= num <= self.max:
                self.orthogonal_chain.update_width(num)
                self.dismiss()
            else:
                self.error_msg.text = "Width must be between between [b]" + str(self.min) + "[/b] and [b]" + \
                                      str(self.max) + "[/b]"
        else:
            self.error_msg.text = "Input must be a positive integer"
