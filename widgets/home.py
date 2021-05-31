from kivy.app import App
from kivy.uix.widget import Widget

from networking.networkthread import NETWORK_INTERFACE
from utils.configuration import CONFIGURATION
from widgets import knob
from widgets.mainmenu import Loading


class Home(Widget):
    def exit_click(self):
        App.get_running_app().manager.show_main_menu()

    def refresh_temperature(self):
        global temp_finish
        temp_finish = False

        def response(res: str):
            if res == "sensor_not_found":
                self.ids["temp_label"].text = "Sensor not present!"
            split = res.split("?")
            self.ids["temp_label"].text = "Temperature: " + split[0] + "C\nHumidity: " + split[1] + "%"
            global temp_finish
            temp_finish = True

        def error():
            self.ids["temp_label"].text = "Connection error!"

        Loading(lambda: NETWORK_INTERFACE.refresh_temperature(response), lambda: temp_finish, error, 5).open(True)

    def refresh_voltage_curr(self):
        global vc_finish
        vc_finish = False

        def response(res: str):
            if res == "sensor_not_found":
                self.ids["vc_label"].text = "Sensor not present!"
            split = res.split("?")
            self.ids["vc_label"].text = "Voltage: " + split[0] + "V\nCurrent: " + split[1] + "A"
            global vc_finish
            vc_finish = True

        def error():
            self.ids["vc_label"].text = "Connection error!"

        Loading(lambda: NETWORK_INTERFACE.refresh_voltage_current(response), lambda: vc_finish, error, 5).open(True)

    def fan_speed_value_change(self, value):
        NETWORK_INTERFACE.set_fans(value)

    def main_brightness_value_change(self, value):
        NETWORK_INTERFACE.set_main_brightness(value*255)

    def on_open(self):
        self.fan_speed_value_change(self.ids["fan_speed_slider"].value)
        self.main_brightness_value_change(self.ids["brightness_slider"].value_normalized)
        self.ids["connection_label"].text = "Connected to:\n"+CONFIGURATION.get_device_name()