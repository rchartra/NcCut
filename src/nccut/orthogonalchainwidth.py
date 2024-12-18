# SPDX-FileCopyrightText: 2024 University of Washington
#
# SPDX-License-Identifier: BSD-3-Clause

"""
Orthogonal chain width adjustment tool.

Creates sidebar element that allows the control of width of orthogonal transects made via the
orthogonal chain tool.
"""

import kivy.uix as ui
from kivy.uix.textinput import TextInput
from kivy.metrics import dp
import nccut.functions as func


class OrthogonalChainWidth(ui.boxlayout.BoxLayout):
    """
    Orthogonal Chain width adjustment tool.

    Creates sidebar element that allows the control of width of orthogonal transects made via the
    orthogonal chain tool.

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
        self.spacing = dp(8)
        self.font_size = orthogonal_chain.home.font
        self.txt = TextInput(hint_text="Width", size_hint=(.7, 1), font_size=self.font_size)
        self.btn = func.RoundedButton(text="Set", size_hint=(.3, 1), font_size=self.font_size)
        self.btn.bind(on_press=lambda x: self.update())
        self.add_widget(self.txt)
        self.add_widget(self.btn)
        self.orthogonal_chain = orthogonal_chain
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
        Update width of current orthogonal chain if given a valid width.
        """
        num = self.txt.text
        if num.isnumeric():
            num = int(num)
            if self.min <= num <= self.max:
                self.orthogonal_chain.update_width(num)
