"""
Class for marker width adjustment tool
"""

import kivy.uix as ui
from kivy.uix.textinput import TextInput
from functions import RoundedButton

class MarkerWidth(ui.boxlayout.BoxLayout):
    # Marker width adjustment widget
    def __init__(self, marker, **kwargs):
        super(MarkerWidth, self).__init__(**kwargs)

        self.txt = TextInput(hint_text="Width", size_hint=(.7, 1))
        self.btn = RoundedButton(text="Go", size_hint=(.3, 1))
        self.btn.bind(on_press=lambda x: self.update())
        self.add_widget(self.txt)
        self.add_widget(self.btn)
        self.marker = marker
        self.spacing = 5

    def update(self):
        # Update width of current marker if given a valid width
        num = self.txt.text
        if num.isnumeric():
            num = int(num)
            if 1 <= num <= 400:
                self.marker.update_width(num)