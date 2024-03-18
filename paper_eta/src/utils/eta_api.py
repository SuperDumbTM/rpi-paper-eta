from typing import Literal

import requests
from flask_babel import lazy_gettext

from ...src import site_data


def route_choices(company: str) -> list[tuple[str]]:
    routes: dict[str, dict] = (
        requests.get(
            f"{site_data.AppConfiguration().get('api_url')}/routes/{company}")
        .json()['data']['routes']
    )
    return [(route['route_no'], route['route_no']) for route in routes.values()]


def direction_choices(company: str,
                      route: str) -> list[tuple[str]]:
    details: dict[str, dict] = (
        requests.get(
            f"{site_data.AppConfiguration().get('api_url')}"
            f"/services/{company}/{route.upper()}")
        .json()['data']
    )

    directions = []
    if details['inbound']:
        directions.append(("inbound", lazy_gettext("inbound")))
    if details['outbound']:
        directions.append(("outbound", lazy_gettext("outbound")))
    return directions


def type_choices(company: str,
                 route: str,
                 direction: str,
                 lang: Literal['en', 'tc'] = 'en') -> list[tuple[str]]:
    details: dict[str, dict] = (
        requests.get(
            f"{site_data.AppConfiguration().get('api_url')}"
            f"/services/{company}/{route.upper()}")
        .json()['data']
    )

    return [(t['service_type'], f"{t['service_type']} ({t['orig']['name'][lang]} -> {t['dest']['name'][lang]})")
            for t in details[direction]]


def stop_choices(company: str,
                 route: str,
                 direction: str,
                 service_type: str,
                 lang: Literal['en', 'tc'] = 'en') -> list[tuple[str]]:
    stops: dict[str, dict] = (
        requests.get(
            f"{site_data.AppConfiguration().get('api_url')}"
            f"/stops/{company}/{route.upper()}",
            {'direction': direction, 'service_type': service_type})
        .json()['data']
    )

    return [(stop['stop_code'], f"{stop['seq']:02}. {stop['name'][lang]}")
            for stop in stops['stops']]
