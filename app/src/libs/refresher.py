import logging
import os
import threading
from io import BytesIO
from pathlib import Path

import requests
from flask_babel import lazy_gettext
from PIL import Image

from app.src import models, site_data
from app.src.libs import epdcon, eta_img

_ctrl_mutex = threading.Lock()


def generate_image(
    app_conf: site_data.AppConfiguration,
    bookmarks: list[models.EtaConfig],
    generator: eta_img.generator.EtaImageGenerator
) -> dict[str, Image.Image]:
    """Generate a ETA image.

    To correctly display the text, call this function with `flask.request`context.

    Args:
        app_config (models.Configuration): _description_
        bookmarks (list[models.EtaConfig]): _description_
        generator (eta_img.eta_image.EtaImageGenerator): _description_

    Returns:
        _type_: _description_
    """
    try:
        etas = []
        for bm in bookmarks:
            res = requests.get(
                app_conf.get('api_url') +
                f'/eta/{bm.company.value}/{bm.route}',
                params={
                    'direction': bm.direction.value,
                    'service_type': bm.service_type,
                    'stop_code': bm.stop_code,
                    'lang': bm.lang,
                }
            ).json()

            try:
                logo = (BytesIO(requests.get('{0}{1}'.format(app_conf.get('api_url'),
                                                             res['data'].pop(
                                                                 'logo_url')
                                                             )).content
                                )
                        if res['data']['logo_url'] is not None
                        else None)
            except Exception:
                logo = None

            if res['success']:
                eta = res['data'].pop('etas')
                etas.append(eta_img.models.Etas(**res['data'],
                                                etas=[eta_img.models.Etas.Eta(**e)
                                                      for e in eta],
                                                logo=logo,
                                                )
                            )
            else:
                res['data'].pop('etas')
                etas.append(eta_img.models.ErrorEta(**res['data'],
                                                    code=res['code'],
                                                    message=str(
                    lazy_gettext(res['code'])),
                    logo=logo,)
                )
        images = generator.draw(etas)
    except requests.RequestException as e:
        logging.warning('Image generation failed with error: %s', str(e))
        images = generator.draw_error('Network Error')
    except Exception as e:
        logging.exception('Image generation failed with error: %s', str(e))
        images = generator.draw_error('Unexpected Error')
    return images


def cached_images(path: os.PathLike) -> dict[str, Image.Image]:
    images = {}
    for path in Path(str(path)).glob('**/*'):
        if path.suffix != '.bmp':
            continue
        images.setdefault(path.name.removesuffix(path.suffix),
                          Image.open(path))
    return images


def display_images(old_images: dict[str, Image.Image],
                   images: dict[str, Image.Image],
                   controller: epdcon.DisplayController,
                   is_partial: bool,
                   wait_if_locked: bool = False,
                   close_display: bool = True) -> None:
    """Display images to the e-paper display.

    This function will ensure that only one refresh at a time.

    Args:
        images (dict[str, Image.Image]): images to be displayed
        controller (display.epaper.DisplayController): e-paper controller
        wait_if_locked (bool, optional): _description_. Defaults to True.
        close_display (bool, optional): _description_. Defaults to True.

    Raises:
        RuntimeError: when not `wait_if_locked` and the 
    """

    # BUG: the implementation is not thread-safe
    if _ctrl_mutex.locked() and not wait_if_locked:
        raise RuntimeError('Lock was aquired.')

    with _ctrl_mutex:
        try:
            controller.initialize()
            if is_partial:
                controller.display_partial(old_images, images)
            else:
                controller.display(images, old_images)
        finally:
            if close_display:
                controller.close()


def clear_screen(controller: epdcon.DisplayController) -> None:
    with _ctrl_mutex:
        try:
            controller.initialize()
            controller.clear()
        finally:
            controller.close()
