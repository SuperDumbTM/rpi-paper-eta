import sys
from pathlib import Path

from PIL import Image

sys.path.append(Path(__file__).parent.parent.parent)

try:
    from .. import controller
except ImportError:
    from epdcon import controller


class Epd1in02(controller.Controller, controller.Partialable):

    _inited = False

    def is_poweron(self) -> bool:
        return type(self)._inited

    @staticmethod
    def partialable() -> bool:
        return True

    def __init__(self, is_partial: bool) -> None:
        super().__init__(is_partial)

        try:
            from .epd_lib import epd1in02
        except ImportError:
            from epd_lib import epd1in02
        self.epdlib = epd1in02.EPD()

    def initialize(self):
        if type(self)._inited:
            return

        if ((self.is_partial and self.epdlib.Init() != 0)
                or (not self.is_partial and self.epdlib.Partial_Init() != 0)):
            raise RuntimeError('Failed to initialize the display.')
        type(self)._inited = True

    def clear(self):
        self.epdlib.Clear()

    def display(self, images: dict[str, Image.Image],):
        if not type(self)._inited:
            raise RuntimeError("The epaper display is not initialized.")
        self.epdlib.display(self.epdlib.getbuffer(images['black']))

    def display_partial(self,
                        old_images: dict[str, Image.Image],
                        images: dict[str, Image.Image]):
        if not type(self)._inited:
            raise RuntimeError("The epaper display is not initialized.")
        if self.is_partial:
            self.epdlib.DisplayPartial(self.epdlib.getbuffer(old_images['black']),
                                       self.epdlib.getbuffer(images['black']))

    def close(self):
        if not type(self)._inited:
            raise RuntimeError("The epaper display is not initialized.")
        self.epdlib.Sleep()
        type(self)._inited = False
