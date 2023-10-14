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

    def text(self, locale: "Locale"):
        if locale == Locale.EN:
            match self:
                case EtaCompany.KMB: "KMB"
                case EtaCompany.MTRBUS: "MTR (Bus)"
                case EtaCompany.MTRLRT: "MTR (Light Rail)"
                case EtaCompany.MTRTRAIN: "MTR"
                case EtaCompany.CTB: "City Bus"
        else:
            match self:
                case EtaCompany.KMB: "九巴"
                case EtaCompany.MTRBUS: "港鐵巴宜"
                case EtaCompany.MTRLRT: "輕鐵"
                case EtaCompany.MTRTRAIN: "港鐵"
                case EtaCompany.CTB: "城巴"


class RouteDirection(str, Enum):
    """Direction of a route"""

    OUTBOUND = "outbound"
    INBOUND = "inbound"


class Locale(str, Enum):
    """Locale codes"""

    TC = "tc"
    EN = "en"
