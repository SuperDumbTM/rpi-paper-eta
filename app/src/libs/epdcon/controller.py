from abc import ABC, abstractmethod

from PIL import Image


class DisplayController(ABC):
    """A uniformed interface to control a e-paper display
    """

    is_partial: bool

    @property
    @abstractmethod
    def is_poweron(self) -> bool:
        """E-paper connection is sill alive (powering on).
        """

    @staticmethod
    def partialable() -> bool:
        """Partial refresh ability of the e-paper display.
        """

    def __init__(self, is_partial: bool = False) -> None:
        self.is_partial = is_partial

    def __enter__(self):
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.close()

    @abstractmethod
    def initialize(self) -> None:
        """Initialize/Power on the e-paper display.
        """

    @abstractmethod
    def clear(self) -> None:
        """Clear the screen of the e-paper display.
        """

    @abstractmethod
    def close(self) -> None:
        """Power off the e-paper display.
        """

    @abstractmethod
    def display(self, imgages: dict[str, Image.Image]) -> None:
        """Display the `images` to the e-paper display.
        """


class Partialable(ABC):

    @abstractmethod
    def display_partial(self,
                        old_images: dict[str, Image.Image],
                        imgages: dict[str, Image.Image]) -> None:
        """Display the `images` to the e-paper display using partial mode.
        """
        pass
