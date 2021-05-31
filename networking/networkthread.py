from concurrent.futures import ThreadPoolExecutor
from threading import Thread

from kivy.app import App

from networking import packetsprocessor
from networking.packets import *
from kivy.logger import Logger, LOG_LEVELS

from networking.networkhelper import *
from utils.configuration import CONFIGURATION
from utils.priorityqueue import PriorityQueue
from time import sleep, time

from typing import Callable, Any

Logger.setLevel(LOG_LEVELS["debug"])

HIGHEST_PRIORITY = 200
HIGH_PRIORITY = 100
MEDIUM_PRIORITY = 50
LOW_PRIORITY = 10
LOWEST_PRIORITY = 1


def null_callback(success, mess):
    Logger.debug("NetworkThread: Nullcallback! Response: " + str(success) + " and msg " + str(mess))
    pass


def _make_future(method_to_execute, return_method=null_callback, *args, **kwargs):
    def internal_future(cancelled=False):
        if cancelled:
            return_method(True, None)
        else:
            print(args)
            return return_method(False, method_to_execute(args, kwargs))

    return internal_future


class NetworkThread(Thread):

    def process_packet(self, packet: ClientBoundPacket):
        clientbound_packets_processors[packet.packet_id](packet, self)
        pass

    def _disconnect_socket(self):
        if self.socket is not None and self.socket:
            self.socket.close()

    def _connect_socket(self, ip_port_tuple):
        try:
            ip, port = ip_port_tuple
            if self.socket is not None:
                self._disconnect_socket()
            if not ping_check(ip):
                return "Ping failed!"
            else:
                self.socket = open_socket(ip, port)
                return "ok"
        except Exception as e:
            Logger.error("NetworkThread: Connections error! Caused: " + str(e))
            return str(e)

    def schedule_future(self, future, priority=MEDIUM_PRIORITY):
        self.queue.push(future, priority)

    def _network_scan(self, *args, **kwargs):
        Logger.debug("NetworkThread: Performing network scan")
        try:
            ip = get_current_default_ip_address_with_mask()
            self.last_scan_result = (
                network_scan(ip, timeout=7))
            Logger.debug("NetworkThread: Scan results: " + str(self.last_scan_result))
        except Exception as e:
            Logger.error("NetworkThread: An error occurred while scanning the network: " + str(e))
            self.last_scan_result = []
        return self.last_scan_result

    def _main_network_task(self):
        pass

    def __init__(self):

        super().__init__()
        self.daemon = True
        self.queue = PriorityQueue()
        self.socket = None
        self.started = True
        self.handshake = False

    def disconnect_socket(self):
        if self.socket is not None:
            self.socket.close()
        self.socket = None
        self.handshake = False

    def run(self):
        Logger.info("Network Thread: Started Network Thread!")
        self.started = True

        while True:
            task = self.queue.dequeue()
            if task is not None:
                try:
                    task()
                except Exception as e:
                    Logger.critical("Critical error in task execution! \n" + str(e))
                    raise e
            self._main_network_task()
            sleep(0.01)

    def has_started(self):
        return self.started

    def send_packet(self, packet: ServerBoundPacket):
        Logger.debug("NetworkThread: Sending packet " + packet.__class__.__name__)
        if isinstance(packet, S03Handshake) or self.active_connection:
            return send(get_packet(packet), self.socket)
        else:
            return "Not connected"

    def _perform_handshake(self):
        result = self.send_packet(S03Handshake(app_version=1))
        if result == "ok":
            timer = time()
            while not self.handshake and time() - timer < 5:
                print(time() - timer)
                sleep(0.5)
            if time() - timer > 5:
                self.disconnect_socket()
                return "Handshake Error"
            else:
                return "ok"
        else:
            return result

    active_connection = property(lambda self: self.socket is not None and self.handshake)

    def disconnect_with_error(self, ex: Exception, reconnect_trials=0):
        self.disconnect_socket()

        def report_error(failure, msg):
            if msg != "ok":
                App.get_running_app().report_connection_error(msg)

        NETWORK_INTERFACE.connect_socket(report_error, NETWORK_INTERFACE.ip, NETWORK_INTERFACE.port, 3)

    def make_handshake(self, packet):
        self.handshake = True
        CONFIGURATION.processCapabilities(packet.text)


class PacketReceiverThread(Thread):

    def __init__(self, nt: NetworkThread):
        super().__init__()
        self.setDaemon(True)
        self.network_thread = nt

    def run(self) -> None:
        Logger.info("PacketsThread: Starting Packet Thread")

        while True:
            if self.network_thread.socket is not None:
                packet = read_packet(self.network_thread.socket)
                if isinstance(packet, ClientBoundPacket):
                    Logger.info("PacketThread: Got a packet " + str(packet))
                    if isinstance(packet, C03Handshake):
                        self.network_thread.make_handshake(packet)
                    else:
                        self.network_thread.schedule_future(lambda: self.network_thread.process_packet(packet))
                if isinstance(packet, Exception):
                    self.network_thread.disconnect_with_error(packet)
            else:
                sleep(0.1)


class NetworkInterface:

    def started(self):
        return self.net.started

    def __init__(self, net: NetworkThread):
        self.port = 48999
        self.ip = ""
        self.net = net

        self.packet_thread = PacketReceiverThread(net)

        self.file_responses = []
        self.sensor_callbacks = []

        Logger.debug("NetworkThread: Initialising Network Instance")

    def start(self):
        if not self.net.is_alive():
            self.net.start()
        if not self.packet_thread.is_alive():
            self.packet_thread.start()

        Logger.debug("NetworkThread: Finished initialising Network Threads")

    def run_network_scan(self, callback: Callable[[bool, Any], None]):
        Logger.debug("NetworkThread: Running network scan")
        callback(False, self.net._network_scan())
        # self.net.schedule_future(_make_future(self.net._network_scan, callback), priority=10)

    @staticmethod
    def run_hostname_discovery(callback: Callable[[bool, tuple], None], ips):
        Logger.debug("NetworkThread: Schedulding network discovery...")

        def internal_hostname(ip):
            Logger.debug("NetworkThread: Searching for hostname for IP: " + str(ip))
            host_name = get_host(ip)
            Logger.debug("NetworkThread: Got " + str(host_name) + " for ip " + str(ip))
            callback(False, (ip, host_name))

        executor = ThreadPoolExecutor()

        for e in ips:
            executor.submit(internal_hostname, e)

    def connect_socket(self, callback: Callable[[bool, str], None], ip, port=48999, trials=0):
        Logger.debug("NetworkThread: Trying to connect to the " + ip + "  with port " + str(port))
        self.port = port
        self.ip = ip

        def connect_perform_handshake(*args, **kwargs):
            result = self.net._connect_socket((ip, port))
            if result != "ok":
                return result
            return self.net._perform_handshake()

        if trials <= 0:
            return self.net.schedule_future(_make_future(connect_perform_handshake, callback), HIGHEST_PRIORITY)
        else:
            def retry_callback(success, msg):
                if msg == "ok":
                    callback(success, msg)
                else:
                    trial = trials - 1
                    self.connect_socket(callback, ip, port, trial)

            return self.net.schedule_future(_make_future(connect_perform_handshake, retry_callback), HIGHEST_PRIORITY)

    def disconnect(self):
        self.net.disconnect_socket()

    def pixel_draw(self, pos_color_tuple, screen_id, height, asynchron=True):
        (x, y), (r, g, b, _) = pos_color_tuple
        r *= 255
        g *= 255
        b *= 255
        y = height - y

        Logger.debug("NetworkThread: Drawing pixel " + str(x) + " " + str(y) + " with color " + str(r) + " " + str(
            g) + " " + str(b))
        packet = S09DrawUpdate(screen_id)
        packet.add_pixel(pixel=(x, y, int(r), int(g), int(b)))

        if asynchron:
            self.net.schedule_future(_make_future(lambda *args, **kwargs: self.net.send_packet(packet)),
                                     HIGHEST_PRIORITY)
        else:
            self.net.send_packet(packet)

    def clear_display(self, screen_id, asynchron=True):
        Logger.debug("NetworkThread: Cleaning display!")
        packet = S09DrawUpdate(screen_id, mode=1)
        if asynchron:
            self.net.schedule_future(_make_future(lambda *args, **kwargs: self.net.send_packet(packet)),
                                     HIGHEST_PRIORITY)
        else:
            self.net.send_packet(packet)

    def file_response(self, p: C05FileResponse):
        found = None

        for entry in self.file_responses:
            if entry[0] == p.request_id:
                found = entry
                break
        if found is None:
            Logger.error("NetworkThread: Unknown packet received! " + str(p.request_id))
        else:
            Logger.debug("NetworkThread: Found response " + str(found))
            self.file_responses.remove(found)
            found[1](p.response)

    def send_file_packet_with_response(self, packet, response):
        self.file_responses.append((packet.request_id, response))
        self.net.send_packet(packet)

    def request_list_dir(self, fn, response):
        self.send_file_packet_with_response(S0CFileOperation(FileOperationType.LS, fn), response)

    def createNewDir(self, path, response):
        self.send_file_packet_with_response(S0CFileOperation(FileOperationType.MKDIR, path), response)

    def delete_file(self, path, response):
        self.send_file_packet_with_response(S0CFileOperation(FileOperationType.DEL, path), response)

    def download(self, to_download, target, download_finished_callback):
        self.send_file_packet_with_response(S0CFileOperation(FileOperationType.DOWN, to_download),
                                            (download_finished_callback, target))

    def file_received(self, packet: C06FileDownload):
        found = None

        for entry in self.file_responses:
            if entry[0] == packet.request_id:
                found = entry
                break
        if found is None:
            Logger.error("NetworkThread: Unknown packet received! " + str(packet.request_id))
        else:
            Logger.debug("NetworkThread: Found response " + str(found))
            self.file_responses.remove(found)
            callback, target = found[1]
            with open(target, mode="bw") as outfile:
                outfile.write(packet.contents)
            callback("sucess!")

    def upload_file(self, path, current_path: str, response):
        if not os.path.exists(path):
            return "File not exists!"
        elif os.path.getsize(path) > 65000:
            return "File too big!"
        if not current_path.endswith("/"):
            current_path += "/"
        packet = S0DFileUpload(current_path + os.path.basename(path))
        packet.readFile(path)
        self.send_file_packet_with_response(packet, response)
        return "ok"
        # TODO

    def sensor_callback(self, packet: C04LogSensor):
        Logger.debug("NetworkInteface: Callback from " + str(packet.sensor_id) + " with id " + str(packet.log_source))
        found = None
        for e in self.sensor_callbacks:
            if e["sensor_id"] == packet.sensor_id and e["log_source"] == packet.log_source:
                found = e
                break
        if found is None:
            Logger.error("NetworkInterface: Found no callback for sensor " + str(packet.sensor_id) + " with id " + str(
                packet.log_source))
        else:
            self.sensor_callbacks.remove(found)
            found["callback"](packet.response)

    def refresh_temperature(self, response):
        # todo: sensors normal numbers
        self.sensor_callbacks.append({"sensor_id": 1, "log_source": 0, "callback": response})
        self.net.send_packet(S05RequestSensor(1))

    def refresh_voltage_current(self, response):
        self.sensor_callbacks.append({"sensor_id": 2, "log_source": 0, "callback": response})
        self.net.send_packet(S05RequestSensor(2))

    def set_fans(self, value):
        self.net.send_packet(S0EControlSet(1, value))  # TODO

    def set_main_brightness(self, value):
        if value < 0:
            value = 0
        if value > 255:
            value = 255
        self.net.send_packet(S0EControlSet(2, value))  # TODO


NETWORK_INTERFACE = NetworkInterface(NetworkThread())
clientbound_packets_processors = {
    3: packetsprocessor.processC03,
    4: lambda packet, _: NETWORK_INTERFACE.sensor_callback(packet),
    5: lambda packet, _: NETWORK_INTERFACE.file_response(packet),
    6: lambda packet, _: NETWORK_INTERFACE.file_received(packet)

}
