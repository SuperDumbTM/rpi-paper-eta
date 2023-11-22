from enum import Enum


class EtaMode(str, Enum):
    MIXED = "mixed"
    ONLY_TIME = "time"
    ONLY_MINUTE = "minute"
