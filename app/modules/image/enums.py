from enum import Enum


class EtaMode(str, Enum):
    MIXED = "mixed"
    TIME = "time"
    MINUTE = "minute"
