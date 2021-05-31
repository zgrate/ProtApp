import os
import socket
from abc import ABC
from enum import Enum
from struct import unpack, pack

from kivy import Logger
from random import randint

from networking.networkhelper import open_socket, send
from utils.utils import crc8
import io


def shortToBytes(short: int) -> bytes:
    return pack("<H", short)


def shortFromBytes(byt: bytes) -> int:
    return unpack("<H", byt)[0]


def stringToBytes(text: str) -> bytes:
    return shortToBytes(len(text)) + bytes(text, encoding="utf-8")


def bytesToString(bytes: bytes) -> str:
    leng = shortFromBytes(bytes[0:2])

    return str(bytes[2:2 + leng], encoding="utf-8")


class FileOperationType(Enum):
    UNKNOWN_OP = 0
    LS = 1
    MKDIR = 2
    TOUCH = 3
    DEL = 4
    MV = 5
    CP = 6
    DOWN = 7


class FileResponseType(Enum):
    UNKNOWN_RESPONSE = 0
    OK_RES = 1
    NOT_FOUND_RES = 2
    INVALID_RES = 3


class SensorType(Enum):
    UNKNOWN_SENSOR = 0
    TEMPERATURE_HUMIDITY = 1
    TEMPERATURE = 2
    HUMIDITY = 3
    CURRENT_VOLTAGE = 4
    IR_RECEIVER = 5
    CONTACTRON = 6
    MAGNETIC_SENSOR = 7
    ADC = 8
    DIGITAL_PIN = 9

    @staticmethod
    def find(iden):
        for k, v in enumerate(SensorType):
            if k == iden:
                return v
        return SensorType.UNKNOWN_SENSOR


# BASE CLASSES
class BasePacket(ABC):

    def __init__(self, packet_id: int):
        self.packet_id = packet_id


class ServerBoundPacket(BasePacket, ABC):

    def prepare_packet_content(self) -> bytes:
        raise NotImplementedError()


class ClientBoundPacket(BasePacket, ABC):

    def construct_packet(self, byt: bytes):
        raise NotImplementedError()


# SERVER BOUND PACKETS


class S03Handshake(ServerBoundPacket):

    def __init__(self, app_version=1):
        super().__init__(3)
        self.app_version = app_version

    def prepare_packet_content(self) -> bytes:
        return bytes([self.app_version])


class S04ChangeAnimation(ServerBoundPacket):
    pass


class S05RequestSensor(ServerBoundPacket):

    def __init__(self, sensor_id):
        super().__init__(5)
        self.sensor_id = sensor_id

    def prepare_packet_content(self) -> bytes:
        return bytes([self.sensor_id])


class S06TimeUpdate(ServerBoundPacket):
    pass


class S07ChangeSystemProperty(ServerBoundPacket):
    pass


class S08ChangeDrawingMode(ServerBoundPacket):
    pass


class S09DrawUpdate(ServerBoundPacket):

    def __len__(self):
        return len(self.pixels) * 7

    def __init__(self, screen_id, mode=0):
        super().__init__(9)
        self.pixels = []
        self.screen_id = screen_id
        self.mode = mode

    def add_pixel(self, pixel: tuple):
        _, _, _, _, _ = pixel
        self.pixels.append(pixel)

    def prepare_packet_content(self) -> bytes:
        byt = bytes([self.screen_id, self.mode]) + pack("<H", len(self.pixels))

        for e in self.pixels:
            x, y, r, g, b = e
            byt += pack("<H", x) + pack("<H", y) + bytes([r, g, b])
        return byt


class S0ARequestShutdown(ServerBoundPacket):
    pass


class S0BRegisterEvent(ServerBoundPacket):
    pass


class S0CFileOperation(ServerBoundPacket):

    def __init__(self, operation: FileOperationType, working_file: str, parameters: str = ""):
        super().__init__(12)
        self.request_id = randint(1, 255)
        self.operation_id = operation.value
        self.working_file = working_file
        self.parameters = parameters

    def prepare_packet_content(self) -> bytes:
        return bytes([self.request_id, self.operation_id]) + stringToBytes(self.working_file) + stringToBytes(
            self.parameters)


class S0DFileUpload(ServerBoundPacket):

    def readFile(self, filename):
        if not os.path.exists(filename):
            return "Not Exists!"
        with open(filename, mode="br") as infile:
            self.buffer = infile.read()

        if len(self.buffer) > 65000:  # TODO: This should be consulted with capabilities
            return "File too large!"

        return "ok"

    def __init__(self, target):
        super().__init__(13)
        self.request_id = randint(1, 255)
        self.target_file = target
        self.buffer = bytes()

    def prepare_packet_content(self) -> bytes:
        return bytes([self.request_id]) + stringToBytes(self.target_file) + self.buffer


class S0EControlSet(ServerBoundPacket):
    def __init__(self, control_id, control_value):
        super().__init__(14)
        self.control_id = control_id
        self.control_value = str(control_value)

    def prepare_packet_content(self) -> bytes:
        return bytes([self.control_id]) + stringToBytes(self.control_value)


# CLIENT BOUND PACKETS
class C03Handshake(ClientBoundPacket):
    def __init__(self):
        super().__init__(3)
        self.text = ""

    def construct_packet(self, bytes: bytes):
        self.text = bytes.decode(encoding="utf-8")


class C04LogSensor(ClientBoundPacket):

    def __init__(self):
        super().__init__(4)
        self.sensor_id = 0
        self.log_source = 0
        self.sensor_type = SensorType.UNKNOWN_SENSOR
        self.response = ""

    def construct_packet(self, byt: bytes):
        self.sensor_id = byt[0]
        self.log_source = byt[1]
        self.sensor_type = SensorType.find(byt[2])
        self.response = bytesToString(byt[3:])


class C05FileResponse(ClientBoundPacket):

    def __init__(self):
        super().__init__(5)
        self.request_id = 0
        self.response_type = FileResponseType.UNKNOWN_RESPONSE
        self.response = ""

    def construct_packet(self, byt: bytes):
        self.request_id = byt[0]
        self.response_type = byt[1]
        self.response = bytesToString(byt[2:])


class C06FileDownload(ClientBoundPacket):

    def __init__(self):
        super().__init__(6)
        self.name = ""
        self.request_id = 0
        self.contents = bytes()

    def construct_packet(self, byt: bytes):
        self.request_id = byt[0]
        self.name = bytesToString(byt[1:])
        self.contents = byt[1 + 2 + len(self.name):]


def get_packet(packet: ServerBoundPacket) -> bytes:
    data = packet.prepare_packet_content()
    finalData = bytes([packet.packet_id]) + pack("<H", len(data))
    finalData += data
    finalData += bytes([crc8(data)])
    return finalData


def read_packet(sock):
    if sock is None:
        return None
    try:
        with sock.makefile(mode="rb") as file:
            try:
                packet_id = (file.read(1))[0]
                Logger.debug(packet_id)
                try:
                    packet = clientbound_packets[packet_id]()
                    data_len_bytes = file.read(2)
                    data_len = unpack("<H", data_len_bytes)[0]
                    Logger.debug("Packets: Decoding packet " + str(packet_id) + " with length " + str(data_len))
                    data_bytes = file.read(data_len)
                    Logger.debug("Packets: Data read! " + str(len(data_bytes)))
                    rec_crc = file.read(1)[0]
                    Logger.debug("Packets: CRC read! " + str(rec_crc))
                    cal_crc = crc8(data_bytes)
                    if cal_crc != rec_crc:
                        Logger.error(
                            "Packets: PACKET DON'T MATCH CRC8! Found: " + str(cal_crc) + " Should be " + str(rec_crc))
                        return None
                    else:
                        packet.construct_packet(data_bytes)
                        Logger.debug("Packets: Packet constructed!")
                        return packet
                except socket.timeout:
                    return None
            except socket.timeout:
                return None
    except Exception as e:
        Logger.error("Packets: A fatal error occured while reading the packet!")
        return e


clientbound_packets = {
    3: C03Handshake,
    4: C04LogSensor,
    5: C05FileResponse,
    6: C06FileDownload

}

# s03 = S03Handshake(1)
# #s.add_pixel((20, 10, 255, 0, 0))
#
# import networking.networkhelper
# import time
#
# s = "TEST"
# l = pack("<H", len(s))
# array = bytes(s, encoding="utf-8")
# crc = 74
# byt = bytes([3, l[0], l[1]] + list(array) + [crc])
# for a in byt:
#     print(a, end=", ")
# print()
# binaryInput = io.BytesIO(byt)
#
# #packet = read_packet(binaryInput)
# #print(packet)
#
#
# from networking.networkhelper import send, open_socket

# contect = get_packet(S0FileOperation(FileOperationType.LS, "/"))
# for e in contect:
#     print(e, end=", ")
# print(contect)
# #exit(0)
# aaaa = S0EControlSet(2, "195")
# # # print(aaaa.readFile("C:\\Users\\dzing\\Desktop\\test2.txt"))
# byt = get_packet(aaaa)
# # # print(byt[-1])
# sock = open_socket("192.168.18.10")
# # send(byt, sock)
# from time import sleep
#
# for i in range(255, 15, -15):
#     print(i)
#     send(get_packet(S0EControlSet(2, i)), sock)
#     sleep(2)
# #
#
# while True:
#     packet = read_packet(sock)
#     #print(packet)
#     if isinstance(packet, C04LogSensor):
#         print(packet.response)
#         send(get_packet(S05RequestSensor(2)), sock)
#         sleep(5)
# #
#
#
# while True:
#     #print(reading.readable())
#     packet = read_packet(sock)
#     print(packet)
#
#     time.sleep(1)
#
#     networking.networkhelper.send(get_packet(s03), sock)
