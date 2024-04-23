from typing import Literal

import requests
from flask_babel import lazy_gettext

from .. import extensions, site_data
from ..libs import hketa


def route_choices(company: str) -> list[tuple[str]]:
    transp = extensions.hketa.create_transport(hketa.Transport(company))
    return [(no, no) for no in transp.route_list().keys()]


def direction_choices(company: str,
                      route: str) -> list[tuple[str]]:
    transp = extensions.hketa.create_transport(hketa.Transport(company))

    directions = []
    if transp.route_list()[route]['inbound']:
        directions.append(("inbound", lazy_gettext("inbound")))
    if transp.route_list()[route]['outbound']:
        directions.append(("outbound", lazy_gettext("outbound")))
    return directions


def type_choices(company: str,
                 route: str,
                 direction: str,
                 lang: Literal['en', 'tc'] = 'en') -> list[tuple[str]]:
    transp = extensions.hketa.create_transport(hketa.Transport(company))
    return [
        (
            t.service_type,
            f"{t.service_type} ({t.orig.name[hketa.Locale(lang)]} -> {t.dest.name[hketa.Locale(lang)]})"
        )
        for t in transp.route_list()[route].bound(hketa.Direction(direction))
    ]


def stop_choices(company: str,
                 route: str,
                 direction: str,
                 service_type: str,
                 lang: Literal['en', 'tc'] = 'en') -> list[tuple[str]]:
    transp = extensions.hketa.create_transport(hketa.Transport(company))
    return [(stop.stop_id, f"{stop.seq:02}. {stop.name[hketa.Locale(lang)]}")
            for stop in transp.stop_list(route, hketa.Direction(direction), service_type)]
