from enum import Enum


class EtaFormat(str, Enum):
    MIXED = "mixed"
    ONLY_TIME = "time"
    ONLY_MINUTE = "minute"
