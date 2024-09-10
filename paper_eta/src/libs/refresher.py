from enum import Enum
from functools import wraps
import logging
import os
import threading
from pathlib import Path
from typing import Callable, Iterable

from PIL import Image
from flask import current_app

from paper_eta.src import site_data

from .. import database, exts
from ..libs import epdcon, hketa, renderer

_ctrl_mutex = threading.Lock()


def partial_tracker():
    log = {"id": None, "count": 0}

    def wrap(schedule: "database.Schedule"):
        if not schedule.is_partial:
            return False
        if schedule.partial_cycle <= 0:
            return True
        if log["id"] != schedule.id:
            log["id"] = schedule.id
            log["count"] = 1
            return False

        log["count"] += 1
        if log["count"] > schedule.partial_cycle:
            log["count"] = 0
            return False
        return True

    return wrap


_is_partial = partial_tracker()


def _with_app_context(func: Callable):
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
    refresh(bookmarks=(database.Bookmark.query
                       .filter(database.Bookmark.bookmark_group_id == schedule.bookmark_group_id)
                       .all()),
            epd_brand=site_data.AppConfiguration()['epd_brand'],
            epd_model=site_data.AppConfiguration()['epd_model'],
            eta_format=(schedule.eta_format.value
                        if isinstance(schedule.eta_format, Enum)
                        else schedule.eta_format),
            layout=schedule.layout,
            is_partial=_is_partial(schedule),
            degree=site_data.AppConfiguration()['degree'],
            is_dry_run=site_data.AppConfiguration()['dry_run'],
            screen_dump_dir=current_app.config['DIR_SCREEN_DUMP'])


def refresh(bookmarks: Iterable["database.Bookmark"],
            epd_brand: str,
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
        renderer_ = renderer.create(epd_brand, epd_model, eta_format, layout)
    except ModuleNotFoundError as e:
        logging.exception(str(e))
        _write_log(**locals(), error_message=str(e))
        return False

    images = renderer_.draw([exts.hketa.create_eta_processor(query).etas()
                             for query in (hketa.RouteQuery(**bm.as_dict()) for bm in bookmarks)],
                            degree)

    try:
        old_screens = load_images(screen_dump_dir)
        is_partial = False if len(old_screens) == 0 else is_partial
        if not is_dry_run:
            controller = epdcon.get(epd_brand,
                                    epd_model,
                                    is_partial=is_partial)
            display_images(old_screens, images, controller, False, True)
    except (OSError, RuntimeError) as e:
        logging.exception("Unable to initialise the e-paper controller.")
        _write_log(**locals(), error_message=str(e))
        return False
    except ModuleNotFoundError as e:
        logging.exception("Controller %s-%s not found", epd_brand, epd_model)
        _write_log(**locals(), error_message=str(e))
        return False
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
    for fpath in Path(str(directory)).glob('*.bmp'):
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

    for filename in current_app.config['DIR_SCREEN_DUMP'].glob("*.*"):
        filename.unlink(True)
