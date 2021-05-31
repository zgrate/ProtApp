from threading import Thread

from kivy.app import App
from kivy.uix.filechooser import FileChooserIconView, FileSystemAbstract
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from time import time, sleep
from os import path
import os
from plyer import filechooser

from networking.networkthread import NETWORK_INTERFACE, Logger
from networking.packets import FileResponseType
from widgets.mainmenu import Loading, InfoPopup

def rfm_debug(text):
    Logger.debug("RemoteFileManager:" + text)


def sanitize_dir(fn):
    return fn.replace("C:\\", "/").replace("\\", "/")

class NewDir(Popup):
    def __init__(self, rfmw, **kwargs):
        super().__init__(**kwargs)
        self.rfmw = rfmw

    def accept(self, text):
        self.dismiss()
        self.rfmw.create_new_dir(text)


class RemoteFileManagerWidget(Widget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rfm = self.ids["rfm"]

    def on_open(self):
        self.rfm.on_open()
      #  self.ids["current_directory"].text = "Directory: " + str(self.rfm.path)

    def on_touch_down(self, touch):
        super().on_touch_down(touch)
#        self.ids["current_directory"].text = "Directory: " + str(self.rfm.path)

    def submit(self):
        if self.rfm.file_system.is_dir(self.rfm.selection[0]):
            self.rfm.path = self.rfm.selection[0]

        # Todo... Something?

    def show_exit(self):
        App.get_running_app().manager.show_main_menu()

    def create_new_dir(self, file):
        rfm_debug("Creating directory " + sanitize_dir(self.rfm.path + file))

        def response(r):
            rfm_debug("Created directory! Response: " + str(r))
            Thread(target=self.rfm.update_files).start()

        NETWORK_INTERFACE.createNewDir(sanitize_dir(self.rfm.path + file), response)

    def show_new_dir(self):
        dir = NewDir(self)
        dir.open()

    def delete_file(self):
        if len(self.rfm.selection) == 0:
            return
        path = sanitize_dir(self.rfm.selection[0])
        if path == "/":
            return

        def response(r):
            rfm_debug("Deleted file! Response: " + str(r))
            Thread(target=self.rfm.update_files).start()

        NETWORK_INTERFACE.delete_file(sanitize_dir(self.rfm.selection[0]), response)

    def enable_buttons(self):
        self.ids["delete_button"].disabled = False
        self.ids["download_button"].disabled = False
        self.ids["delete_button"].opacity = 1
        self.ids["download_button"].opacity = 1

    def disable_buttons(self):
        self.ids["delete_button"].disabled = True
        self.ids["download_button"].disabled = True
        self.ids["delete_button"].opacity = 0.2
        self.ids["download_button"].opacity = 0.2

    def download_file(self):
        if len(self.rfm.selection) == 0:
            return

        file = sanitize_dir(self.rfm.selection[0])
        if self.rfm.file_system.is_dir(file):
            return

        split = (file.split("."))
        if len(split) > 1:
            fil = ["."+split[-1]]
        else:
            fil = []

        split2 = file.split("/")


        def handle_selection(selection):
            if selection is None or len(selection) == 0:
                return
            to_download = file
            rfm_debug("Downloading file " + to_download + " to " + selection[0])
            if fil != [] and not to_download.endswith(fil[0]):
                to_download += fil[0]

            if path.exists(selection[0]):
                os.remove(selection[0])

            global finished
            finished = False

            def download_finished(response):
                rfm_debug("Downloaded file!")
                global finished
                finished = True

            def error_download():
                Logger.error("RemoteFileManager: File Download error!")

            Loading(lambda: NETWORK_INTERFACE.download(to_download, selection[0], download_finished), lambda: finished, error_download, 30).open(True)

        filechooser.save_file(on_selection=handle_selection, path=split2[-1], filters=fil, multiple=False, title="Select download target")

    def upload_file(self):
        def handle_selection(selection):
            if len(selection) == 0:
                return

            def response(response):
                rfm_debug("Got response " + str(response))
                InfoPopup("Upload Completed!", "Upload successfull!", on_dismiss=lambda _:self.rfm.update_files()).open()
                #self.rfm.update_files()

            res = NETWORK_INTERFACE.upload_file(selection[0], sanitize_dir(self.rfm.path), response)
            if res != "ok":
                InfoPopup("Error", "Error: " + str(res)).open()
        filechooser.open_file(on_selection=handle_selection,  multiple=False, title="Select file to upload")





class RemoteFileSystem(FileSystemAbstract):

    def __init__(self):
        self.lastDir = []
        self.li = []
        self.directory = "/"
        self.last_popup = None

    def listdir(self, fn):
        rfm_debug("Listing directory of " + str(fn))
        if not NETWORK_INTERFACE.net.active_connection:
            return []
        fn = sanitize_dir(fn)

        if self.directory == fn and len(self.li) != 0:
            return self.li

        rfm_debug("Downloading new update!...")
        self.directory = fn
        self.lastDir = []
        self.li = []
        self.finished = False

        def response(dir_response: str):
            Logger.debug("RFM: Response is " + str(dir_response))
            if dir_response.startswith("E;"):

                for widget in App.get_running_app().root_window.children:
                    if isinstance(widget, Popup):
                        self.finished = True
                        return
                Popup(title="Error!", size_hint=(0.5, 0.4), content=Label(text="Error while retrieving files!\nPlease make sure you set pullups and\nthe SD card is inserted!")).open()


            else:
                for e in dir_response.split("?"):
                    if e == "":
                        continue
                    split = e.split(":")
                    d = {"type": split[0]}
                    if d["type"] == "F":
                        d["size"] = int(split[1])
                        d["name"] = split[2]
                    else:
                        d["name"] = split[1]
                    self.lastDir.append(d)
                    self.li.append(d["name"])

            self.finished = True

        rfm_debug("Sending request to list directory...")

        def error():
            Logger.error("RemoteFileManager: Error with a packet!")
            # TODO: Do something

        Loading(lambda: NETWORK_INTERFACE.request_list_dir(fn, response), lambda: self.finished, error, 10).open(False)
        #
        #
        # while not self.finished and time() - timer < 10000:
        #     print("waiting...")
        #     sleep(0.1)
        # if not self.finished:
        #     Logger.error("RemoteFileManager: Error with a packet!")
        return self.li

    def getsize(self, fn: str):
        file = sanitize_dir(fn)
        for e in self.lastDir:
            if e["name"] == file:
                if "size" in e:
                    return e["size"]
                else:
                    return 0
        Logger.error("RemoteFileManager: Error! File not found in the list! " + str(fn))
        return 0

    def is_dir(self, fn):
        file = sanitize_dir(fn)
        for e in self.lastDir:
            if e["name"] == file:
                return e["type"] == "D"
        Logger.error("RemoteFileManager: Error! File not found in the list! " + str(fn))
        return True

    def is_hidden(self, fn):
        return False

    pass


class RemoteFileManager(FileChooserIconView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.file_system = RemoteFileSystem()

    def update_files(self):
        self.file_system.directory = ""
        self._update_files()

    def on_open(self):
        self.path = "/"

    def entry_touched(self, entry, touch):
        super().entry_touched(entry, touch)
        self.parent.parent.enable_buttons()

