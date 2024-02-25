import pydantic
from flask_babel import lazy_gettext

from app.src import enums


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
