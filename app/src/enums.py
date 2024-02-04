import io
from enum import Enum
from pathlib import Path
from typing import Literal


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

    def text(self, locale: "EtaLocale"):
        if locale == EtaLocale.EN:
            match self:
                case EtaCompany.KMB: return "KMB"
                case EtaCompany.MTRBUS: return "MTR (Bus)"
                case EtaCompany.MTRLRT: return "MTR (Light Rail)"
                case EtaCompany.MTRTRAIN: return "MTR"
                case EtaCompany.CTB: return "City Bus"
        else:
            match self:
                case EtaCompany.KMB: return "九巴"
                case EtaCompany.MTRBUS: return "港鐵巴士"
                case EtaCompany.MTRLRT: return "輕鐵"
                case EtaCompany.MTRTRAIN: return "港鐵"
                case EtaCompany.CTB: return "城巴"

    def icon(self, color: Literal['bw', 'c', 'bw_neg']) -> io.BufferedReader:
        base = Path(__file__).parent.joinpath(
            'static', 'images', 'logos', color)
        return open(base.joinpath(f'{self.value}.bmp'), "rb")


class RouteDirection(str, Enum):
    """Direction of a route"""

    OUTBOUND = "outbound"
    INBOUND = "inbound"


class EtaLocale(str, Enum):
    """Locale for ETA texts"""

    TC = "tc"
    EN = "en"
