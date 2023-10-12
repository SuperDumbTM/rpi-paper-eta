from enum import Enum


class FlashCategory(str, Enum):
    info = "info"
    success = "success"
    warn = "warning"
    error = "error"


class EtaCompany(str, Enum):
    """Company identifier for transport companies"""

    KMB = "kmb"
    MTRBUS = "mtr_bus"
    MTRLRT = "mtr_lrt"
    MTRTRAIN = "mtr_train"
    CTB = "ctb"


class RouteDirection(str, Enum):
    """Direction of a route"""

    OUTBOUND = "outbound"
    INBOUND = "inbound"


class Locale(str, Enum):
    """Locale codes"""

    TC = "tc"
    EN = "en"
