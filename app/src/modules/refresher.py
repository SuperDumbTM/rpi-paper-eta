import base64
import logging
from io import BytesIO
import os
from pathlib import Path
import threading

import requests
from PIL import Image

from app.src import models, site_data, translation
from app.src.modules import image as eimage
from app.src.modules import display


_ctrl_mutex = threading.Lock()


def generate_image(
    app_conf: site_data.AppConfiguration,
    bookmarks: list[models.EtaConfig],
    generator: eimage.eta_image.EtaImageGenerator
) -> dict[str, Image.Image]:
    """Generate a ETA image.

    To correctly display the text, call this function with `flask.request`context.

    Args:
        app_config (models.Configuration): _description_
        bookmarks (list[models.EtaConfig]): _description_
        generator (eimage.eta_image.EtaImageGenerator): _description_

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
                                                   message=str(translation.RP_CODE_TRANSL.get(
                                                       res['code'], res['message'])),
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
        with open(path, 'rb') as f:
            if path.suffix != '.bmp':
                continue
            images[path.name.removesuffix(path.suffix)] = base64.b64encode(
                f.read()).decode("utf-8")
    return images


def display_images(old_images: dict[str, Image.Image],
                   images: dict[str, Image.Image],
                   controller: display.epaper.DisplayController,
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
            controller.display(images, old_images)
        finally:
            if close_display:
                controller.close()