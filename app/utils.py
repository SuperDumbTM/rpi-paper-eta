import dataclasses
import json
import logging
import random
import string
from enum import Enum
from io import BytesIO
from pathlib import Path

import requests
from flask import request, url_for
from flask_babel import lazy_gettext
from PIL import Image

from app import config, translation
from app.modules import image as eimage


def singleton(class_: object):
    """A singleton class decorator"""
    instances = {}

    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]
    return getinstance


def redirect_url(default='index'):
    return request.args.get('next') or request.referrer or url_for(default)


def asdict_factory(data):
    """
    `dataclass.asdict` factory that supports `Enum` convertion

    Reference: https://stackoverflow.com/a/64693838"""
    def convert_value(obj):
        if isinstance(obj, Enum):
            return obj.value
        return obj
    return dict((k, convert_value(v)) for k, v in data)


def random_id_gen(length: int) -> str:
    """Generate strings composed with uppercase and digits.
    """
    return ''.join(random.choice(string.ascii_uppercase + string.digits)
                   for _ in range(length))

# ------------------------------------------------------------
#                       API requests
# ------------------------------------------------------------


def route_choices(company: str) -> list[tuple[str]]:
    routes: dict[str, dict] = (
        requests.get(
            f"{config.site_data.AppConfiguration().get('url')}/{company}/routes")
        .json()['data']['routes']
    )
    return [(route['name'], route['name']) for route in routes.values()]


def direction_choices(company: str,
                      route: str) -> list[tuple[str]]:
    details: dict[str, dict] = (
        requests.get(
            f"{config.site_data.AppConfiguration().get('url')}"
            f"/{company}/{route.upper()}")
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
                 direction: str) -> list[tuple[str]]:
    details: dict[str, dict] = (
        requests.get(
            f"{config.site_data.AppConfiguration().get('url')}"
            f"/{company}/{route}")
        .json()['data']
    )

    return [(t['service_type'], f"{t['service_type']} ({t['orig']['name']['tc']} -> {t['dest']['name']['tc']})")
            for t in details[direction]]


def stop_choices(company: str,
                 route: str,
                 direction: str,
                 service_type: str) -> list[tuple[str]]:
    stops: dict[str, dict] = (
        requests.get(
            f"{config.site_data.AppConfiguration().get('url')}"
            f"/{company}/{route.upper()}/{direction}/{service_type}/stops")
        .json()['data']
    )

    return [(stop['stop_code'], f"{stop['seq']:02}. {stop['name']['tc']}")
            for stop in stops['stops']]


class DataclassJSONEncoder(json.JSONEncoder):
    """JSON encoder with `dataclass` encoding support"""
    def default(s, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)
