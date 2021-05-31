from kivy.config import Config
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import ButtonBehavior
from kivy.uix.image import Image

from widgets.connectmenu import *
from widgets.home import Home
from widgets.mainmenu import *
from widgets.paint import *
from widgets.remotefilemanager import RemoteFileManagerWidget
from widgets.selectablelist import *
from widgets.settingsmenu import SettingsMenu

Builder.load_file("kvs/main.kv")
Builder.load_file("kvs/paint.kv")
Builder.load_file("kvs/home.kv")
Builder.load_file("kvs/settings.kv")
Builder.load_file("kvs/connect_menu.kv")
Builder.load_file("kvs/remotefilemanager.kv")

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

async def test():
    print("EXTERNAL!")
    await asyncio.sleep(1)


class ImageButton(ButtonBehavior, Image):
    pass


class InterfaceManager(BoxLayout):

    # def __init__(self, **kwargs):
    #     super().__init__(**kwargs)
    # self.painting = PaintingMode()#(16, 8)

    def show_main_menu(self):
        self.clear_widgets()
        self.add_widget(self.main_menu)
        self.main_menu.on_open()



    def show_file_manager(self):
        self.clear_widgets()
        self.add_widget(self.file_manager)
        self.file_manager.on_open()

    def show_painting_widget(self, clear_all=False):
        self.clear_widgets()
        self.add_widget(self.painting)
        self.painting.on_open(clear_all)
        # print(self.size)
        # self.painting.drawLines()
        # self.painting.buildGUI(self.size)

    def show_color_picker(self, current_color):
        self.clear_widgets()
        self.add_widget(self.color_choose)
        self.color_choose.set_color(current_color)

    def show_home_menu(self):
        self.clear_widgets()
        self.add_widget(self.home)
        self.home.on_open()

    def show_settings_menu(self):
        self.clear_widgets()
        self.add_widget(self.settings_menu)

    def show_connect_menu(self):
        self.clear_widgets()
        self.add_widget(self.connect_menu)
        self.connect_menu.on_start()


class CommandsDispatcher:

    def __init__(self, app):
        self.app = app

    def color_pick(self, current_color=(0, 0, 0)):
        self.app.manager.show_color_picker(current_color)

    def accept_color(self, new_color):
        r, g, b, a = new_color
        self.app.manager.painting.color = (r, g, b, a)
        self.app.manager.show_painting_widget()

    def deny_color(self):
        self.app.manager.show_painting_widget()

    def creator_mode_press(self, clear=False):
        self.app.manager.show_painting_widget(clear_all=clear)

    def main_menu(self):
        self.app.manager.show_main_menu()

    def exit(self):
        self.app.stop()

    def home_menu_press(self):
        self.app.manager.show_home_menu()

    def settings_menu_press(self):
        self.app.manager.show_settings_menu()

    def file_manager_press(self):
        self.app.manager.show_file_manager()

    def ask_disconnect(self):
        AskDisconnect().open()
        pass



class MainApp(App):

    title = "ProtApp"

    icon = "images/icon.jpg"

    def report_connection_error(self, ex: Exception):
        Logger.error("Main: An error occured while performing connection!")
        pop = Popup(title="Error!", content=Label(text="Connection error. Reason: " + str(ex)),
                    size_hint=(0.5, 0.5))
        pop.open()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.commander = CommandsDispatcher(self)
        self.manager = InterfaceManager()
        self.manager.main_menu = MainMenu()
        self.manager.home = Home()
        self.manager.connect_menu = ConnectMenu()
        self.manager.painting = PaintingMode(128, 32)
        self.manager.color_choose = ColorPickerObject()
        self.manager.settings_menu = SettingsMenu()
        self.manager.file_manager = RemoteFileManagerWidget()

        # self.paintWidget = PaintingWidget(16, 8)

    def disconnect(self, popup):
        popup.dismiss()
        NETWORK_INTERFACE.disconnect()
        del CONFIGURATION["last_connection"]
        self.manager.show_connect_menu()

    def build(self):
        Logger.debug("Main:Finished initialization!")
        NETWORK_INTERFACE.start()
        return self.manager

    def on_start(self):

        if CONFIGURATION.exists("last_connection"):
            connect_with_popout(CONFIGURATION["last_connection"]["last_ip"], error_callback=self.manager.show_connect_menu, show_error=False)
        else:
            self.manager.show_connect_menu()
        #self.manager.show_file_manager()
        #self.manager.show_main_menu()


if __name__ == '__main__':
    MainApp().run()


