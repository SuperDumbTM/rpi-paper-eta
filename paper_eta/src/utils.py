import base64
from io import BytesIO
from typing import Literal, Optional

import PIL.Image
from flask import request
from flask_babel import lazy_gettext

from paper_eta.src import extensions
from paper_eta.src.libs import hketa


def route_choices(transport: str) -> list[tuple[str]]:
    transp = extensions.hketa.create_transport(hketa.Transport(transport))
    return [(no, no) for no in transp.route_list().keys()]


def direction_choices(transport: str,
                      no: str) -> list[tuple[str]]:
    transp = extensions.hketa.create_transport(hketa.Transport(transport))

    directions = []
    if transp.route_list()[no].inbound:
        directions.append(
            (hketa.Direction.INBOUND.value, lazy_gettext("inbound")))
    if transp.route_list()[no].outbound:
        directions.append(
            (hketa.Direction.OUTBOUND.value, lazy_gettext("outbound")))
    return directions


def type_choices(transport: str,
                 no: str,
                 direction: str,
                 locale: Literal['en', 'tc'] = 'en') -> list[tuple[str]]:
    transp = extensions.hketa.create_transport(hketa.Transport(transport))

    return [
        (
            t.service_type,
            f"{t.service_type} "
            f"({t.orig.name[hketa.Locale(locale)]} -> {t.dest.name[hketa.Locale(locale)]})"
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


def get_locale() -> Optional[str]:
    crrt_locale = (request.cookies.get('locale')
                   or request.headers.get("X-Locale"))
    translations = [str(translation)
                    for translation in extensions.babel.list_translations()]

    if crrt_locale in translations:
        return crrt_locale

    return request.accept_languages.best_match(translations)


def img2b64(img: PIL.Image.Image) -> str:
    """Convert a PIL image to base64 encoded string."""
    b = BytesIO()
    img.save(b, 'bmp')
    return base64.b64encode(b.getvalue()).decode('utf-8')
