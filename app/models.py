from typing import Optional

from pydantic.dataclasses import dataclass

from app import enums


@dataclass(slots=True)
class EtaConfig:
    company: enums.EtaCompany
    route: str
    direction: enums.RouteDirection
    service_type: str
    stop_code: str
    lang: str
    id: Optional[str] = None


@dataclass(slots=True)
class EpdConfig:
    brand: str
    model: str
    layout: str
    style: str
