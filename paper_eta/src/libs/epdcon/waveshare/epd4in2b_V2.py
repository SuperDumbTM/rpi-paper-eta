import sys
from pathlib import Path

from PIL import Image

sys.path.append(Path(__file__).parent.parent.parent)

try:
    from .. import controller
except ImportError:
    from epdcon import controller


class Controller(controller.Controller):

    _inited = False

    @property
    def is_poweron(self) -> bool:
        return type(self)._inited

    @staticmethod
    def partialable() -> bool:
        return False

    def __init__(self, is_partial: bool) -> None:
        super().__init__(is_partial)
        try:
            from .epd_lib import epd4in2b_V2
        except ImportError:
            from epd_lib import epd4in2b_V2
        self.epdlib = epd4in2b_V2.EPD()

    def initialize(self):
        if type(self)._inited:
            return
        if self.epdlib.init() != 0:
            raise RuntimeError('Failed to initialize the display.')
        type(self)._inited = True

    def clear(self):
        self.epdlib.Clear()

    def display(self, images: dict[str, Image.Image]):
        if not type(self)._inited:
            raise RuntimeError("The epaper display is not initialized.")
        self.epdlib.display(self.epdlib.getbuffer(images['0-0-0']),
                            self.epdlib.getbuffer(images['255-0-0']))

    def close(self):
        if not type(self)._inited:
            raise RuntimeError("The epaper display is not initialized.")
        self.epdlib.sleep()
        type(self)._inited = False
