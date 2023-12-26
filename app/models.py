from typing import Optional

import pydantic

from app import enums


class EtaConfig(pydantic.BaseModel):
    company: enums.EtaCompany
    route: str
    direction: enums.RouteDirection
    service_type: str
    stop_code: str
    lang: str
    id: Optional[str] = None


class Schedule(pydantic.BaseModel):
    id: str
    schedule: str
    eta_type: str
    layout: str
    is_partial: bool
    enabled: bool = True
