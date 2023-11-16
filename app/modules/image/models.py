import datetime
from typing import Any, Optional
from pydantic import BaseModel


class Etas(BaseModel):
    route: str
    origin: str
    destination: str
    stop_name: str
    logo: str
    timestamp: datetime.datetime
    etas: Optional[list["Eta"]] = None

    class Eta(BaseModel):
        company: str
        destination: str
        is_arriving: bool
        eta: datetime.datetime
        eta_minute: int
        remark: Optional[str]
        extras: Optional[dict[str, Any]]


class ErrorEta(BaseModel):
    code: str
    message: str

    route: str
    origin: str
    destination: str
    stop_name: str
    logo: str
    timestamp: datetime.datetime
