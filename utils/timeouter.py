import threading
from random import Random
from threading import Thread
from time import sleep

from kivy.logger import Logger

_random = Random()
_timeout_queue = {}


class StoppableCancelTimeouter(Thread):

    def __init__(self, cancel_callback, timeout=5, description=None, daemon=False):
        super().__init__()
        self.daemon = daemon
        self.stopped = False
        self.cancel_callback = cancel_callback
        self.timeout_time = timeout
        self.description = description

    def run(self) -> None:
        sleep(self.timeout_time)
        if self.stopped:
            Logger.debug("Timeouter: Callback has been cancelled " + str(self.description))
        else:
            if self.description is None:
                Logger.warning("Timeouter: Got a timeout from unknown timeouter")
            else:
                Logger.warning("Timeouter: Got a timeout from " + str(self.description))
            self.cancel_callback()

    def cancel(self):
        self.stopped = True


def cancel_task(identification):
    for i in threading.enumerate():
        if i.ident == identification and type(i) is StoppableCancelTimeouter:
            i.cancel()


def set_timeout(cancel_callback, timeout_time=5, description=None):
    _thread = StoppableCancelTimeouter(cancel_callback, timeout_time, description, True)
    _thread.start()
    return _thread.ident
