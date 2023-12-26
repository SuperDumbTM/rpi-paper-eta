import dataclasses
import json
import logging
import random
import string
from enum import Enum
from io import BytesIO

import requests
from flask import current_app, request, url_for
from flask_babel import lazy_gettext
from PIL import Image

from app import config
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
            f"{config.site_data.ApiServerSetting().url}/{company}/routes")
        .json()['data']['routes']
    )
    return [(route['name'], route['name']) for route in routes.values()]


def direction_choices(company: str,
                      route: str) -> list[tuple[str]]:
    details: dict[str, dict] = (
        requests.get(
            f"{config.site_data.ApiServerSetting().url}/{company}/{route.upper()}")
        .json()['data']
    )

    directions = []
    if details['inbound']:
        directions.append((lazy_gettext("inbound"), "inbound"))
    if details['outbound']:
        directions.append((lazy_gettext("outbound"), "outbound"))
    return directions


def type_choices(company: str,
                 route: str,
                 direction: str) -> list[tuple[str]]:
    details: dict[str, dict] = (
        requests.get(
            f"{config.site_data.ApiServerSetting().url}/{company}/{route}")
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
            f"{config.site_data.ApiServerSetting().url}/{company}/{route.upper()}/{direction}/{service_type}/stops")
        .json()['data']
    )

    return [(stop['stop_code'], f"{stop['seq']:02}. {stop['name']['tc']}")
            for stop in stops['stops']]


# ------------------------------------------------------------
#                           E-paper
# ------------------------------------------------------------


def generate_image(eta_type: eimage.enums.EtaType, layout: str) -> dict[str, Image.Image]:
    """Generate an ETA image

    Args:
        eta_type (eimage.enums.EtaType): ETA type
        layout (str): information layout name

    Returns:
        dict[str, Image.Image]: generated image(s)
    """
    api_setting = config.site_data.ApiServerSetting()
    bm_setting = config.site_data.BookmarkList()
    epd_setting = config.site_data.EpaperSetting()
    generator = eimage.eta_image.EtaImageGeneratorFactory().get_generator(
        epd_setting.brand, epd_setting.model
    )(eta_type, layout)

    try:
        etas = []
        for bm in bm_setting:
            res = requests.get(
                f'{api_setting.url}/{bm.company.value}/{bm.route}/{bm.direction.value}/etas',
                params={
                    'service_type': bm.service_type,
                    'lang': bm.lang,
                    'stop': bm.stop_code}
            ).json()

            logo = (BytesIO(requests.get('{0}{1}'.format(api_setting.url,
                                                         res['data'].pop(
                                                             'logo_url')
                                                         )).content
                            )
                    if res['data']['logo_url'] is not None
                    else None)

            if res['success']:
                eta = res['data'].pop('etas')
                etas.append(eimage.models.Etas(**res['data'],
                                               etas=[eimage.models.Etas.Eta(**e)
                                                     for e in eta],
                                               logo=logo,
                                               )
                            )
            else:
                res['data'].pop('etas')
                etas.append(eimage.models.ErrorEta(**res['data'],
                                                   code=res['code'],
                                                   message=res['message'],
                                                   logo=logo,)
                            )
        images = generator.draw(etas)
    except requests.RequestException as e:
        logging.warning(f'Image generation failed with error: {str(e)}')
        images = generator.draw_error('Network Error')
    except Exception as e:
        logging.exception(f'Image generation failed with error: {str(e)}')
        images = generator.draw_error('Unexpected Error')

    generator.write_images(config.flask_config.CACHE_DIR, images)
    return images


class DataclassJSONEncoder(json.JSONEncoder):
    """JSON encoder with `dataclass` encoding support"""
    def default(s, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)
