import datetime
from typing import Optional

import pydantic

from app import enums
from app.modules import image as eimage


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


class RefreshLog(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

    timestamp: datetime.datetime
    eta_type: eimage.enums.EtaType
    layout: str
    is_partial: bool
    error: Optional[BaseException] = None
