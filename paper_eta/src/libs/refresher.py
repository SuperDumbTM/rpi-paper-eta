import logging
import os
import threading
from io import BytesIO
from pathlib import Path

import requests
from flask_babel import lazy_gettext
from PIL import Image

from .. import extensions, models, site_data
from ..libs import epdcon, eta_img, hketa

_ctrl_mutex = threading.Lock()


def generate_image(
    bookmarks: list[hketa.models.RouteQuery],
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
            etap = extensions.hketa.create_eta_processor(bm)
            route = eta_img.Route(**bm.model_dump(),
                                  origin=etap.route.orig_name(),
                                  destination=etap.route.dest_name(),
                                  stop_name=etap.route.stop_name(),
                                  logo=etap.route.logo(),
                                  etas=[])

            try:
                for eta in etap.etas():
                    route.etas.append(eta_img.Route.Eta(**eta.model_dump()))
            except hketa.exceptions.HketaException as e:
                route.etas = eta_img.Route.Error(message=str(e))

            etas.append(route)

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
                   controller: epdcon.Controller,
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
            if controller.is_partial and issubclass(type(controller), epdcon.Partialable):
                controller.display_partial(old_images, images)
            else:
                controller.display(images)
        finally:
            if close_display:
                controller.close()


def clear_screen(controller: epdcon.Controller) -> None:
    with _ctrl_mutex:
        try:
            controller.initialize()
            controller.clear()
        finally:
            controller.close()
