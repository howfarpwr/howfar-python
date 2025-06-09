import ctypes
import time
from typing import Iterable


class HowFarSettings(ctypes.LittleEndianStructure):
    """
    Binary representation of struct Settings from settings.h.
    """

    _fields_ = [
        ("settingsVersion", ctypes.c_uint32),
        ("featureALS", ctypes.c_uint16, 1),
        ("featureTOF", ctypes.c_uint16, 1),
        ("featureDCDCSleep", ctypes.c_uint16, 1),
        ("featureStorage", ctypes.c_uint16, 1),
        ("_featurePadding", ctypes.c_uint16, 12),
        ("flagEraseDatabase", ctypes.c_uint16, 1),
        ("_flagPadding", ctypes.c_uint16, 15),
        ("timestamp", ctypes.c_uint32),
        ("tofDistanceMode", ctypes.c_uint32),
        ("tofTimingBudget", ctypes.c_uint32),
        ("measurementInterval", ctypes.c_uint32),
        ("examinationIdentifier", ctypes.c_char * 8),
    ]

    def get(self, key):
        value = getattr(self, key)
        # adapt types
        if isinstance(value, bytes):
            value = value.decode("ASCII")
        # fixup values
        if key == "examinationIdentifier":
            value = value.rstrip(" ")
        return value

    def set(self, key, value):
        # ensure the key is valid
        current_value = self.get(key)
        # fixup values
        if key == "examinationIdentifier":
            value = value.ljust(8, " ")
        # adapt types
        if isinstance(current_value, str):
            value = value.encode("ASCII")
        else:
            value = int(value)
        setattr(self, key, value)

    def keys(self) -> Iterable[str]:
        for field in self._fields_:
            name = field[0]
            if name.startswith("_"):
                continue
            yield name

    def pack(self):
        return bytes(self)

    @classmethod
    def defaults(cls):
        return cls(
            settingsVersion=2024091701,
            featureALS=1,
            featureTOF=1,
            featureDCDCSleep=0,
            featureStorage=1,
            _featurePadding=0,
            flagEraseDatabase=0,
            _flagPadding=0,
            timestamp=int(time.time()),
            tofDistanceMode=1,
            tofTimingBudget=20,
            measurementInterval=10,
            examinationIdentifier=b"OPTODATA",
        )
