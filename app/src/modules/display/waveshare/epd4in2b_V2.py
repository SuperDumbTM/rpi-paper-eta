import sys
from pathlib import Path

from PIL import Image

sys.path.append(Path(__file__).parent.parent.parent)

try:
    from .. import epaper
except ImportError:
    from display import epaper


class Epd4in2bV2(epaper.DisplayController):

    _inited = False

    def is_poweron(self) -> bool:
        return type(self)._inited

    @staticmethod
    def partialable() -> bool:
        return False

    def __init__(self, is_partial: bool, is_dryrun: bool = False) -> None:
        super().__init__(is_partial, is_dryrun)

        if is_dryrun:
            return

        try:
            from .epd_lib import epd4in2b_V2
        except ImportError:
            from epd_lib import epd4in2b_V2
        self.epdlib = epd4in2b_V2.EPD()

    def initialize(self):
        if type(self)._inited or self.is_dryrun:
            return
        if self.epdlib.init() != 0:
            raise RuntimeError('Failed to initialize the display.')
        type(self)._inited = True

    def clear(self):
        if self.is_dryrun:
            return
        self.epdlib.Clear()

    def display(self, images: dict[str, Image.Image], old_images: dict[str, Image.Image] = None):
        if self.is_dryrun:
            return
        if not type(self)._inited:
            raise RuntimeError("The epaper display is not initialized.")

        self.epdlib.display(self.epdlib.getbuffer(images['black']),
                            self.epdlib.getbuffer(images['red']))

    def close(self):
        if not type(self)._inited or self.is_dryrun:
            return
        self.epdlib.sleep()
        type(self)._inited = False
