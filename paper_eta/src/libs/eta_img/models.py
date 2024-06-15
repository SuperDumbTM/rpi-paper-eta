import datetime
from io import BytesIO
from typing import Any, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from paper_eta.src import enums


class Route(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    no: str
    origin: str
    destination: str
    stop_name: str
    locale: enums.EtaLocale
    logo: Optional[BytesIO] = None
    etas: Union[list["Eta"], "Error"]
    timestamp: datetime.datetime = Field(
        default=datetime.datetime.now().astimezone())

    class Eta(BaseModel):
        destination: str
        is_arriving: bool
        eta: datetime.datetime
        remark: Optional[str]
        extras: Optional[dict[str, Any]]

    class Error(BaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)

        message: str
