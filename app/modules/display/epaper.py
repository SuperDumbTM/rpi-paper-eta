from abc import ABC, abstractmethod

from PIL import Image


class DisplayController(ABC):
    """A uniformed interface to control a e-paper display
    """

    is_partial: bool
    is_dryrun: bool

    @property
    @abstractmethod
    def is_poweron(self) -> bool:
        """E-paper connection is sill alive (powering on)"""

    @staticmethod
    def partialable() -> bool:
        """Partial refresh ability of the e-paper display"""

    def __init__(self, is_partial: bool = False, is_dryrun: bool = False) -> None:
        self.is_partial = is_partial
        self.is_dryrun = is_dryrun

    def __enter__(self):
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.close()

    @abstractmethod
    def initialize(self) -> None:
        """Initialize/Power on the e-paper display"""

    @abstractmethod
    def clear(self) -> None:
        """Clear the screen of the e-paper display"""

    @abstractmethod
    def close(self) -> None:
        """Power off the e-paper display"""

    @abstractmethod
    def display(self, imgages: dict[str, Image.Image]) -> None:
        """Display the `images` to the e-paper display

        Args:
            imgages (dict[str, Image.Image]): \
                *key representing the color of the image
        """


class ControllerFactory:

    @classmethod
    def brands(cls) -> tuple[str]:
        return ("waveshare",)

    @classmethod
    def models(cls, brand: str) -> list[type[DisplayController]]:
        try:
            import waveshare
        except ImportError:
            from . import waveshare

        match brand:
            case "waveshare":
                return waveshare.epapers
        raise KeyError(f"Unrecognized epaper brand: {brand}")

    @classmethod
    def get_controller(cls, brand: str, model: str) -> type[DisplayController]:
        models = cls.models(brand)

        for controller in models:
            if model == controller.__name__:
                return controller
        raise KeyError(f"Unrecognized epaper: {brand}-{model}")
