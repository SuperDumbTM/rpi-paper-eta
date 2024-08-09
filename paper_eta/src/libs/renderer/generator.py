from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Iterable, NamedTuple, TypedDict, Union

import PIL.Image

from ..hketa import Eta, Locale

FONT_BASE_PATH = Path(__file__).parent.joinpath("_fonts")


class RendererSpec(TypedDict):
    class Description(TypedDict):
        en: str
        zh_Hant_HK: str

    class Graphics(TypedDict):
        en: Iterable[str]
        zh_Hant_HK: Iterable[str]

    width: Union[int, float]
    height: Union[int, float]
    color: dict[str, tuple[int, int, int]]
    description: Description
    graphics: Graphics


class EtaFormat(str, Enum):
    MIXED = "mixed"
    ABSOLUTE = "absolute"
    RELATIVE = "relative"


class ImageRenderer(ABC):

    format: EtaFormat

    @classmethod
    @abstractmethod
    def spec(cls) -> RendererSpec:
        pass

    @abstractmethod
    def draw(self,
             etas: Iterable[Eta],
             degree: float = 0) -> dict[str, PIL.Image.Image]:
        """Create image(s) with the ETA(s) data
        """

    @abstractmethod
    def draw_error(self, message: str, degree: float = 0) -> dict[str, PIL.Image.Image]:
        pass

    # def write_images(self, directory: os.PathLike, images: dict[str, Image.Image]):
    #     logging.info("saving display output to file(s)")

    #     if not os.path.exists(directory):
    #         logging.warning("%s do not exist, creating...", directory)
    #         os.makedirs(directory)

    #     for color, image in images.items():
    #         image.save(os.path.join(directory, f"{color}.bmp"))
    #         logging.debug("%s.bmp created", color)

    # def read_images(self, directory: os.PathLike) -> dict[str, Image.Image]:
    #     logging.info("reading display output(s) from file(s)")

    #     images = {}
    #     for color in self.colors:
    #         images[color] = Image.open(os.path.join(directory, f"{color}.bmp"))
    #     return images
