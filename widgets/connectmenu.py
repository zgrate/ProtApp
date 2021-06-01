import re

from kivy.app import App
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget

from networking.networkthread import NETWORK_INTERFACE
from utils.configuration import CONFIGURATION
from widgets.mainmenu import Loading, InfoPopup

Builder.load_string("<PleaseWaitPopup@Popup>:\n"
                    "   title:'Please wait'\n"
                    "   auto_dismiss: False\n"
                    "   size_hint: (0.5,0.5)\n"
                    "   GridLayout:\n"
                    "      cols:1\n"
                    "      Label:\n"
                    "         id: message_label\n"
                    "         text: 'wait'\n"
                    # "      Button:\n"
                    # "         id: button_ok\n"
                    # "         text: 'OK'\n"
                    # "         on_release: root.ok_click()\n"
                    # "         size_hint: (0.2, 0.2)\n"
                    # "         disabled: True"
                    "   "
                    "   ")

Builder.load_string("<ManualIPPopout@Popup>:\n"
                    "   title:'Please type in IP Address'\n"
                    "   auto_dismiss: False\n"
                    "   size_hint: (0.5,0.5)\n"
                    "   GridLayout:\n"
                    "      cols:1\n"
                    "      Label:\n"
                    "         size_hint: (1, 0.5)\n"
                    "         id: message_label\n"
                    "         text: 'Type in the IP Address \\n Default port: 48999'\n"
                    "      TextInput:\n"
                    "         size_hint: (1, 0.1)\n"
                    "         multiline: False\n"
                    "         id: ip_input\n"
                    "         suggestion_text: 'TEST'\n"
                    "         padding: 5\n"
                    "      GridLayout:\n"
                    "         padding: 5\n"
                    "         rows:1\n"
                    "         size_hint: (1, 0.3)\n"
                    "         ImageButton:\n"
                    "            size_hint: (1, 0.2)\n"
                    "            source: 'images/accept.png'\n"
                    "            text: 'Connect'\n"
                    "            on_release: root.connect()\n"
                    "         ImageButton:\n"
                    "            on_release: root.cancel()\n"
                    "            source: 'images/decline.png'\n"
                    "            size_hint: (1, 0.2)\n"
                    "            text: 'Cancel'")


class ManualIPPopout(Popup):

    def __init__(self, connect_callback, **kwargs):
        super().__init__(**kwargs)
        self.callback = connect_callback

    def connect(self):
        Logger.debug("ConnectMenu: Got manual value: " + str(self.ids["ip_input"].text))
        self.callback(str(self.ids["ip_input"].text).lstrip())
        self.dismiss()

    def cancel(self):
        self.dismiss()
        Logger.info("ConnectMenu: Canceled manual IP Input!")


class PleaseWaitPopup(Popup):
    def __init__(self, ok_callback=lambda: Logger.debug("ConnectMenu: OK!"),
                 message_text="Please wait for an action to complete...",
                 ok_button="Dissmiss", block_enable=True, **kwargs):
        super().__init__(**kwargs)
        self.ok_click_call = ok_callback
        self.ids["message_label"].text = message_text

    def ok_click(self):
        self.ok_click_call()
        self.dismiss()

    pass


class ConnectMenu(Widget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.has_finished = False

    def rescan_button(self):
        self.scan()

    def accept_button(self):
        Logger.debug("ConnectMenu: ACCEPTED IP " + self.ip)
        connect_with_popout(self.ip)

    #        future.add_done_callback(internal_accept_callback)

    def scan(self):

        self.has_finished = False

        def network_scan_results(cancelled, response):
            self.has_finished = True
            if not cancelled:
                l = list(map(lambda d: "(" + d + ")", response))
                self.ids["list_addresses"].put_data_single(l, self.select_data)

                def set_data_on_pos_future(cancelled_internal, ip_host):
                    if not cancelled_internal:
                        ip, host = ip_host
                        self.ids["list_addresses"].set_data_on_pos(l.index("(" + ip + ")"), host + "(" + ip + ")")

                NETWORK_INTERFACE.run_hostname_discovery(set_data_on_pos_future, response)

        def error():
            Logger.error("Connect Menu: Network Discovery error!")
            InfoPopup(title="Error!", text="Network Discovery error!\nPlease provide IP address!").open()
            self.ids["list_addresses"].put_data_single([], self.select_data)

        def start_task():
            NETWORK_INTERFACE.run_network_scan(lambda b, res: network_scan_results(b, res))

        Loading(start_task, lambda: self.has_finished, error, 7, "Scanning the network...").open(True)

    def on_start(self):
        self.scan()
        # NETWORK_THREAD.network_scan_callback =

    def select_data(self, data: dict):
        self.ip = (re.findall("\((.*)\)", string=data["text"])[0])
        self.ids["accept_button"].disabled = False
        self.ids["accept_button"].opacity = 1

    @staticmethod
    def manual_ip_popout():
        popout = ManualIPPopout(connect_callback=connect_with_popout)
        popout.open()


def connect_with_popout(ip: str, show_error: bool = True, error_callback=None):
    port = 48999
    if ":" in ip:
        sp = ip.split(":")
        ip = sp[0]
        port = int(sp[1])

    # if error_callback is None:
    #     def error():
    #         InfoPopup(title="Error!", text="Error connecting!\nReason: Connection timeout!").open()
    #
    #     error_callback = error

    global connect_finished
    connect_finished = False

    def internal_accept_callback(_, response=""):
        global connect_finished
        connect_finished = True
        Logger.info("ConnectMenu: Connection completed! Result:\n" + str(response))
        if response == "ok":
            CONFIGURATION["last_connection"] = {"last_ip": ip}
            App.get_running_app().manager.show_main_menu()
            return
        del CONFIGURATION["last_connection"]
        if show_error:
            InfoPopup(title="Error!", text="Error connecting! Reason:\n" + str(response)).open()
        if error_callback is not None:
            error_callback()

    Loading(lambda: NETWORK_INTERFACE.connect_socket(internal_accept_callback, ip, port), lambda: connect_finished,
            error_callback, 6, "Connecting to " + str(ip)).open(True)
