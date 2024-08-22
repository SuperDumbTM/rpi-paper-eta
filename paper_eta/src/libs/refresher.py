from enum import Enum
from functools import wraps
import logging
import os
import threading
from pathlib import Path

from PIL import Image
from flask import current_app

from paper_eta.src import site_data

from .. import database, exts
from ..libs import epdcon, hketa, renderer

_ctrl_mutex = threading.Lock()

_refresh_rotate = {
    "id": None,
    "count": 0
}


def _with_app_context(func):
    """Decorator function that wraps the input function with an Flask application context.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # reference: https://stackoverflow.com/a/73618460
        with exts.scheduler.app.app_context():
            return func(*args, **kwargs)
    return wrapper


def _write_log(**kwargs):
    exts.db.session.add(
        database.RefreshLog(
            eta_format=kwargs["eta_format"],
            layout=kwargs["layout"],
            is_partial=kwargs["is_partial"],
            error_message=kwargs.get("error_message")
        ))
    exts.db.session.commit()


@_with_app_context
def scheduled_refresh(schedule: "database.Schedule"):
    """Function that handles scheduled refresh based on the input schedule.

    Args:
        schedule: The schedule object containing information about the data refresh.
    """
    if not schedule.is_partial:
        is_partial = False
    elif schedule.partial_cycle <= 0:
        is_partial = True
    elif _refresh_rotate["id"] != schedule.id:
        _refresh_rotate["id"] = schedule.id
        _refresh_rotate["count"] = 1
        is_partial = False
    else:
        _refresh_rotate["count"] += 1
        is_partial = True
        if _refresh_rotate["count"] > schedule.partial_cycle:
            _refresh_rotate["count"] = 0
            is_partial = False

    refresh(epd_brand=site_data.AppConfiguration()['epd_brand'],
            epd_model=site_data.AppConfiguration()['epd_model'],
            eta_format=(schedule.eta_format.value
                        if isinstance(schedule.eta_format, Enum)
                        else schedule.eta_format),
            layout=schedule.layout,
            is_partial=is_partial,
            degree=site_data.AppConfiguration()['degree'],
            is_dry_run=site_data.AppConfiguration()['dry_run'],
            screen_dump_dir=current_app.config['DIR_SCREEN_DUMP'])


@_with_app_context
def refresh(epd_brand: str,
            epd_model: str,
            eta_format: str,
            layout: str,
            is_partial: bool,
            degree: int,
            is_dry_run: bool,
            screen_dump_dir: Path) -> bool:
    if eta_format not in (t for t in renderer.EtaFormat):
        logging.error("Invalid Eta Format: %s", eta_format)
        _write_log(**locals(), error_message="Invalid Eta Formate.")
        return False

    # ---------- generate ETA images ----------
    try:
        renderer_ = renderer.create(
            epd_brand, epd_model, eta_format, layout)
    except ModuleNotFoundError as e:
        logging.exception(str(e))
        _write_log(**locals(), error_message=str(e))
        return False

    queries = [hketa.RouteQuery(**bm.as_dict())
               for bm in database.Bookmark.query
               .filter(database.Bookmark.enabled)
               .order_by(database.Bookmark.ordering)
               .all()]

    images = renderer_.draw([exts.hketa.create_eta_processor(query).etas()
                             for query in queries],
                            degree)

    if not is_dry_run:
        # ---------- initialise the e-paper controller ----------
        try:
            controller = epdcon.get(
                epd_brand, epd_model, is_partial=is_partial)
        except (OSError, RuntimeError) as e:
            logging.exception("Unable to initialise the e-paper controller.")
            _write_log(**locals(), error_message=str(e))
            return False
        except ModuleNotFoundError as e:
            logging.exception(str(e))
            _write_log(**locals(), error_message=str(e))
            return False

        # ---------- refresh the e-paper screen ----------
        try:
            display_images(load_images(screen_dump_dir),
                           images,
                           controller,
                           False,
                           True)
        except Exception as e:  # pylint: disable=broad-exception-caught
            _write_log(**locals(), error_message=str(e))
            if isinstance(e, RuntimeError):
                logging.error(str(e))
            else:
                logging.exception(
                    "An unexpected error occurred during screen refreshing.")
            return False

    _write_log(**locals())
    for color, image in images.items():
        image.save(screen_dump_dir.joinpath(f"{color}.bmp"), "bmp")
    return True


def load_images(directory: os.PathLike) -> dict[str, Image.Image]:
    images = {}
    for fpath in Path(str(directory)).glob('**/*'):
        if fpath.suffix != '.bmp':
            continue
        images.setdefault(fpath.name.removesuffix(fpath.suffix),
                          Image.open(fpath))
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
