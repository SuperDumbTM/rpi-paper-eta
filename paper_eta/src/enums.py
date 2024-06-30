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
    NLB = "nlb"

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

    def iso(self) -> str:
        match self:
            case EtaLocale.TC:
                return "zh_HK"
            case EtaLocale.EN:
                return "en_US"
