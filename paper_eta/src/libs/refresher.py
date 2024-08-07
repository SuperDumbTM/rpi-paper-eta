import logging
import os
import threading
from pathlib import Path

from PIL import Image

from .. import database, extensions
from ..libs import epd_log, epdcon, hketa, renderer

_ctrl_mutex = threading.Lock()


def refresh(epd_brand: str,
            epd_model: str,
            eta_format: str,
            layout: str,
            is_partial: bool,
            is_dry_run: bool):
    args_snap = locals()

    if eta_format not in (t for t in renderer.EtaFormat):
        logging.error(
            "Failed to refresh the screen due to invalid EtaFormat: %s", eta_format)
        return

    # ---------- generate ETA images ----------

    # reference: https://stackoverflow.com/a/73618460
    with extensions.scheduler.app.app_context():
        queries = [hketa.RouteQuery(**bm.as_dict())
                   for bm in database.Bookmark.query
                   .filter(database.Bookmark.enabled)
                   .order_by(database.Bookmark.ordering)
                   .all()]
        etas = []
        for query in queries:
            etap = extensions.hketa.create_eta_processor(query)
            etas.append(etap.etas())
        images = extensions.imgen.render(epd_brand,
                                         epd_model,
                                         eta_format,
                                         layout,
                                         etas
                                         )

    if not is_dry_run:
        # ---------- initialise the e-paper controller ----------
        try:
            controller = epdcon.get(
                epd_brand, epd_model, is_partial=is_partial)
        except (OSError, RuntimeError) as e:
            logging.exception("Cannot initialise the e-paper controller.")
            epd_log.epdlog.put(epd_log.Log(**args_snap, error=e))
            return

        # ---------- refresh the e-paper screen ----------
        try:
            display_images(extensions.imgen.load(),
                           images,
                           controller,
                           False,
                           True)
        except Exception as e:  # pylint: disable=broad-exception-caught
            epd_log.epdlog.put(epd_log.Log(**args_snap, error=e))

            if isinstance(e, RuntimeError):
                logging.warning(
                    "Failed to refresh the screen due to %s.", str(e))
            else:
                logging.exception(
                    "An unexpected error occurred during display refreshing.")
            return

    epd_log.epdlog.put(epd_log.Log(**args_snap))
    extensions.imgen.save(images)
    return


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
