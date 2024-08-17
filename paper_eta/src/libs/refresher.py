import logging
import os
import threading
from pathlib import Path

from PIL import Image

from .. import database, exts
from ..libs import epdcon, hketa, renderer

_ctrl_mutex = threading.Lock()


def _write_log(**kwargs):
    with exts.scheduler.app.app_context():
        exts.db.session.add(
            database.RefreshLog(
                eta_format=kwargs["eta_format"],
                layout=kwargs["layout"],
                is_partial=kwargs["is_partial"],
                error_message=kwargs.get("error_message")
            ))
        exts.db.session.commit()


def refresh(epd_brand: str,
            epd_model: str,
            eta_format: str,
            layout: str,
            is_partial: bool,
            degree: int,
            is_dry_run: bool,
            screen_dump_dir: Path) -> bool:
    if eta_format not in (t for t in renderer.EtaFormat):
        logging.error("Invalid EtaFormat: %s", eta_format)
        _write_log(**locals(), error_message=str(e))
        return False

    # ---------- generate ETA images ----------
    try:
        renderer_ = renderer.create(
            epd_brand, epd_model, eta_format, layout)
    except ModuleNotFoundError as e:
        logging.exception(str(e))
        _write_log(**locals(), error_message=str(e))
        return False

    # reference: https://stackoverflow.com/a/73618460
    with exts.scheduler.app.app_context():
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
