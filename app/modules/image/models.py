import datetime
from io import BytesIO
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class Etas(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    route: str
    origin: str
    destination: str
    stop_name: str
    logo: Optional[BytesIO] = None
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
    model_config = ConfigDict(arbitrary_types_allowed=True)

    code: str
    message: str

    route: str
    origin: str
    destination: str
    stop_name: str
    logo: Optional[BytesIO] = None
    timestamp: datetime.datetime
