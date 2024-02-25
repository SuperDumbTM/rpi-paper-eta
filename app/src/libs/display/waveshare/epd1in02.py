import sys
from pathlib import Path

from PIL import Image

sys.path.append(Path(__file__).parent.parent.parent)

try:
    from .. import epaper
except ImportError:
    from display import epaper


class Epd1in02(epaper.DisplayController):

    _inited = False

    def is_poweron(self) -> bool:
        return type(self)._inited

    @staticmethod
    def partialable() -> bool:
        return True

    def __init__(self, is_partial: bool, is_dryrun: bool = False) -> None:
        super().__init__(is_partial, is_dryrun)

        if is_dryrun:
            return

        try:
            from .epd_lib import epd1in02
        except ImportError:
            from epd_lib import epd1in02
        self.epdlib = epd1in02.EPD()

    def initialize(self):
        if type(self)._inited or self.is_dryrun:
            return

        if ((self.is_partial and self.epdlib.Init() != 0)
                or (not self.is_partial and self.epdlib.Partial_Init() != 0)):
            raise RuntimeError('Failed to initialize the display.')
        type(self)._inited = True

    def clear(self):
        if self.is_dryrun:
            return
        self.epdlib.Clear()

    def display(self, images: dict[str, Image.Image], old_images: dict[str, Image.Image]):
        if self.is_dryrun:
            return
        if not type(self)._inited:
            raise RuntimeError("The epaper display is not initialized.")
        if self.is_partial:
            self.epdlib.DisplayPartial(self.epdlib.getbuffer(old_images['black']),
                                       self.epdlib.getbuffer(images['black']))
        else:
            self.epdlib.display(self.epdlib.getbuffer(images['black']))

    def close(self):
        if not type(self)._inited or self.is_dryrun:
            return
        self.epdlib.Sleep()
        type(self)._inited = False
