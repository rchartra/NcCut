# SPDX-FileCopyrightText: 2024 University of Washington
#
# SPDX-License-Identifier: BSD-3-Clause

"""
Marker width adjustment tool.

Creates sidebar element that allows the control of width of orthogonal transects made via the
transect marker tool.
"""

import kivy.uix as ui
from kivy.uix.textinput import TextInput
from kivy.metrics import dp
import nccut.functions as func


class MarkerWidth(ui.boxlayout.BoxLayout):
    """
    Marker width adjustment tool.

    Creates sidebar element that allows the control of width of orthogonal transects made via the
    transect marker tool.

    Attributes:
        spacing: The spacing between widgets in the layout
        txt: kivy.uix.textinput.TextInput widget where user enters their desired width
        btn: 'Set' Button
        marker: Current :class:`nccut.multimarker.MultiMarker` instance
        min (int): Minimum width allowed
        max (int): Maximum width allowed
    """
    def __init__(self, marker, **kwargs):
        """
        Defines graphical elements.

        Args:
            marker: Active :class:`nccut.multimarker.MultiMarker` instance
        """
        super(MarkerWidth, self).__init__(**kwargs)
        self.spacing = dp(8)
        self.font_size = marker.home.font
        self.txt = TextInput(hint_text="Width", size_hint=(.7, 1), font_size=self.font_size)
        self.btn = func.RoundedButton(text="Set", size_hint=(.3, 1), font_size=self.font_size)
        self.btn.bind(on_press=lambda x: self.update())
        self.add_widget(self.txt)
        self.add_widget(self.btn)
        self.marker = marker
        self.min = 1
        self.max = 400

    def font_adapt(self, font):
        """
        Update go button font size

        Args:
            font (float): New font size
        """
        self.btn.font_size = font

    def update(self):
        """
        Update width of current marker if given a valid width.
        """
        num = self.txt.text
        if num.isnumeric():
            num = int(num)
            if self.min <= num <= self.max:
                self.marker.update_width(num)
