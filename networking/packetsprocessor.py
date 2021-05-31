from networking import packets
from utils.configuration import CONFIGURATION
from kivy.logger import Logger


def processC03(packet: packets.C03Handshake, networkThread):
    Logger.debug("PacketsProcessor: Processing packet C03Handshake!")
    networkThread.make_handshake(packet)
