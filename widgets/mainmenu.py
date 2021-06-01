from threading import Thread
from time import time, sleep

from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget

from utils.configuration import CONFIGURATION


class AskDisconnect(Popup):
    pass


class InfoPopup(Popup):
    def __init__(self, title="Info", text="Information!", **kwargs):
        super().__init__(title=title, size_hint=(0.4, 0.4), content=Label(text=text), **kwargs)


class Loading(ModalView):
    def __init__(self, to_execute, response_waiter, error_callback, wait_time, loading_text="Loading...", **kwargs):
        super().__init__(**kwargs)
        self.to_execute = to_execute
        # self.callback = callback
        self.response_waiter = response_waiter
        self.error_callback = error_callback
        self.wait_time = wait_time
        self.ids["loading_text"].text = loading_text

    def _task(self):
        self.to_execute()
        timer = time()
        while not self.response_waiter() and time() - timer < self.wait_time:
            sleep(0.1)

        if time() - timer > self.wait_time:
            self.error_callback()

        self.dismiss()

    def open(self, asyn=False, *largs, **kwargs):
        super().open()
        if asyn:
            Thread(target=self._task).start()
        else:
            self._task()

    pass


class MainMenu(Widget):

    def on_open(self):
        self.ids["connection_label"].text = "Connected to:\n" + CONFIGURATION.get_device_name()

    pass
