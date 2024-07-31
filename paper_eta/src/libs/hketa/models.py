from datetime import datetime
from io import BytesIO
from typing import Any, Optional, Union

import pydantic
import pytz

try:
    from . import enums
except (ImportError, ModuleNotFoundError):
    import enums


class RouteQuery(pydantic.BaseModel):

    transport: enums.Company
    no: str
    """route number"""
    direction: enums.Direction
    stop_id: str
    """stop ID"""
    service_type: str
    locale: enums.Locale


class RouteInfo(pydantic.BaseModel):

    transport: enums.Company
    route_no: str
    inbound: list["Detail"] = pydantic.Field(default_factory=list)
    outbound: list["Detail"] = pydantic.Field(default_factory=list)

    def bound(self, bound: enums.Direction) -> list["Detail"]:
        return (self.inbound
                if bound == enums.Direction.INBOUND else self.outbound)

    def service_lookup(self, bound: enums.Direction, service_type: str) -> "Detail":
        for detail in self.bound(bound):
            if detail.service_type == service_type:
                return detail
        raise KeyError(f"Invalid service type: {service_type}")

    class Detail(pydantic.BaseModel):

        service_type: str
        route_id: Optional[str] = None
        orig: Optional["RouteInfo.Stop"] = None
        dest: Optional["RouteInfo.Stop"] = None

    class Stop(pydantic.BaseModel):

        stop_id: str
        seq: int
        name: dict[enums.Locale, str]


class Eta(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

    no: str
    origin: str
    destination: str
    stop_name: str
    locale: enums.Locale
    logo: Optional[BytesIO] = None
    etas: Union[list["Time"], "Error"]
    timestamp: datetime = pydantic.Field(
        default=datetime.now().replace(tzinfo=pytz.timezone('Etc/GMT-8')))

    class Time(pydantic.BaseModel):
        destination: str
        is_arriving: bool
        """Indicate whether the vehicle in the vincity of to the stop.
        """
        is_scheduled: bool
        """Indicate whether the ETA is based on realtime information or based on schedule.
        """
        eta: datetime
        remark: Optional[str] = None
        extras: Optional[dict[str, Any]] = None

    class Error(pydantic.BaseModel):
        message: str
