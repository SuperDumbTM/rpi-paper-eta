from enum import Enum


class EtaType(str, Enum):
    MIXED = "mixed"
    ONLY_TIME = "time"
    ONLY_MINUTE = "minute"
