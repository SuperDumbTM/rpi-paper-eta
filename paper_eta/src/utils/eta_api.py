from typing import Literal

from flask_babel import lazy_gettext

from .. import extensions
from ..libs import hketa


def route_choices(transport: str) -> list[tuple[str]]:
    transp = extensions.hketa.create_transport(hketa.Transport(transport))
    return [(no, no) for no in transp.route_list().keys()]


def direction_choices(transport: str,
                      no: str) -> list[tuple[str]]:
    transp = extensions.hketa.create_transport(hketa.Transport(transport))

    directions = []
    if transp.route_list()[no].inbound:
        directions.append(("inbound", lazy_gettext("inbound")))
    if transp.route_list()[no].outbound:
        directions.append(("outbound", lazy_gettext("outbound")))
    return directions


def type_choices(transport: str,
                 no: str,
                 direction: str,
                 locale: Literal['en', 'tc'] = 'en') -> list[tuple[str]]:
    transp = extensions.hketa.create_transport(hketa.Transport(transport))

    return [
        (
            t.service_type,
            f"{t.service_type} ({t.orig.name[hketa.Locale(locale)]} -> {t.dest.name[hketa.Locale(locale)]})"
        )
        for t in transp.route_list()[no].bound(hketa.Direction(direction))
    ]


def stop_choices(transport: str,
                 no: str,
                 direction: str,
                 service_type: str,
                 locale: Literal['en', 'tc'] = 'en') -> list[tuple[str]]:
    transp = extensions.hketa.create_transport(hketa.Transport(transport))
    return [(stop.stop_id, f"{stop.seq:02}. {stop.name[hketa.Locale(locale)]}")
            for stop in transp.stop_list(no, hketa.Direction(direction), service_type)]
