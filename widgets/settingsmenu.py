from buildozer import JsonStore
from kivy.uix.widget import Widget


class SettingsMenu(Widget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.store = JsonStore("config.json")
        self.store["test"] = "Testujemy"
        self.store["eleven"] = 11

