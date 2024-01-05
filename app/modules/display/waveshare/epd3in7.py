import logging
import threading

from PIL import Image

try:
    from .. import epaper
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(Path(__file__).parent.parent)
    from display import epaper


class Epd3in7(epaper.DisplayController):

    _inited = False
    _mutex = threading.Lock()

    def is_poweron(self) -> bool:
        return type(self)._inited

    @staticmethod
    def partialable() -> bool:
        return True

    def __init__(self, is_partial: bool) -> None:
        super().__init__(is_partial)
        try:
            from .lib import epd3in7
        except ImportError:
            from display.waveshare.lib import epd3in7

        self.epdlib = epd3in7.EPD()

    def initialize(self):
        if type(self)._inited:
            return

        if ((self.is_partial and self.epdlib.init(1) != 0)
                or (not self.is_partial and self.epdlib.init(0) != 0)):
            raise RuntimeError('Failed to initialize the display.')
        type(self)._inited = True

    def clear(self):
        if self.is_partial:
            self.epdlib.Clear(0xFF, 0)
        else:
            self.epdlib.Clear(0xFF, 1)

    def display(self, images: dict[str, Image.Image]):
        if not type(self)._inited:
            raise RuntimeError("The epaper display is not initialized.")

        with type(self)._mutex:
            if self.is_partial:
                self.epdlib.display_1Gray(
                    self.epdlib.getbuffer(images['black']))
            else:
                self.epdlib.display_4Gray(
                    self.epdlib.getbuffer_4Gray(images['black']))

    def close(self):
        if not type(self)._inited:
            return

        self.epdlib.sleep()
        type(self)._inited = False
