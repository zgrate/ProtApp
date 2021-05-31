from kivy.storage.jsonstore import JsonStore
from kivy.logger import Logger
from enum import Enum
from json import loads


class ScreenType(Enum):
    PX_RGB = 1
    MAX_MONO = 2
    WS_RGB = 3
    NON_ADDRESABLE_RGB = 4
    MONO_LED = 5

    class ColorType(Enum):
        RGB_24bit = 1
        RGB_8bit = 2
        MONOCHROMATIC = 3

    class BulkMode(Enum):
        CHAIN = 1
        BULK_2x2 = 2


class Sensors(Enum):
    UNKNOWN = 0
    TEMPERATURE_HUMIDITY = 1
    TEMPERATURE = 2
    HUMIDITY = 3
    CURRENT_VOLTAGE = 4
    IR_RECEIVER = 5
    CONTACTRON = 6
    MAGNETIC_SENSOR = 7
    ADC = 8
    DIGITAL_PIN = 9


class Controls(Enum):
    FAN = 1
    LASER = 2
    IR_TRANSMITTER = 3
    DAC = 4
    DIGITAL_PIN = 5
    OLED = 6


class NonExceptionDictionary:
    def __init__(self, json_string):
        if type(json_string) is str:
            self.dictionary = loads(json_string)
        elif type(json_string) is dict:
            self.dictionary = json_string

    def __getitem__(self, item):
        if item not in self.dictionary:
            return None
        else:
            it = self.dictionary[item]
            if type(it) is dict:
                return NonExceptionDictionary(it)
            else:
                return it


class ConfigStore:
    def __init__(self, file="config.json"):
        self.store = JsonStore(file)

    def __getitem__(self, item):
        return self.store[item]

    def __setitem__(self, key, value):
        self.store[key] = value

    def __delitem__(self, key):
        try:
            self.store.delete(key)
        except KeyError:
            pass

    def exists(self, key):
        return self.store.exists(key)

    def processCapabilities(self, text:str):
        Logger.debug("Configuration: Processing Capabilities...")
        #TODO

    def get_device_name(self):
        return "VISS_ZOS_DEV"
        #TODO



CONFIGURATION = ConfigStore("config.json")
