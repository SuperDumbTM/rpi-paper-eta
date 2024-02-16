import datetime
from typing import Optional

import croniter
import pydantic
from flask_babel import lazy_gettext

from app.src import enums
from app.src.modules import image as eimage


class EtaConfig(pydantic.BaseModel):
    company: enums.EtaCompany
    route: str
    direction: enums.RouteDirection
    service_type: str
    stop_code: str
    lang: str

    def model_dump_i18n(self) -> dict:
        return self.model_dump() | {
            k: lazy_gettext(v) for k, v in self.model_dump(exclude=['route', 'stop_code', 'id']).items()
        }


class Schedule(pydantic.BaseModel):
    # This model is intened to be use only by `RefreshScheduler`, and the ID field will be filled by the class.

    id: str
    schedule: str
    eta_type: eimage.enums.EtaType
    layout: str
    is_partial: bool = False
    enabled: bool = True

    def model_dump_i18n(self) -> dict:
        return self.model_dump() | {'eta_type': lazy_gettext(self.eta_type)}

    @pydantic.field_validator('schedule')
    @classmethod
    def check_cron_expression(cls, v: str):
        if (not croniter.croniter.is_valid(v)):
            raise ValueError('invalid cron expression')
        return v

    # @pydantic.root_validator
    # def check_layout(cls, values):
    #     eta_type, layout = values.get('eta_type'), values.get('layout')
    #     return values


class RefreshLog(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

    timestamp: datetime.datetime = pydantic.Field(
        default_factory=datetime.datetime.now)
    eta_type: eimage.enums.EtaType
    layout: str
    is_partial: bool
    error: Optional[BaseException] = None

    def model_dump_i18n(self) -> dict:
        return self.model_dump() | {'eta_type': lazy_gettext(self.eta_type.value)}


class Configuration(pydantic.BaseModel):
    # API server setting
    url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    # e-paper setting
    epd_brand: Optional[str] = None
    epd_model: Optional[str] = None