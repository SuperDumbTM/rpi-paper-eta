import collections
import os
from pathlib import Path
import sys
import json
import logging
from abc import ABC, abstractmethod
from typing import Iterable

from PIL import Image, ImageFont

try:
    import enums
    import models
except ImportError:
    from . import enums, models


class EtaImageGenerator(ABC):

    eta_type: enums.EtaType
    # _data: dict[str, dict]
    fonts: "FontLoader"

    @property
    @abstractmethod
    def colors(self) -> Iterable[str]:
        """Color name that the generator will using in generating the image"""
        pass

    @classmethod
    def layouts(cls) -> dict[enums.EtaType, list[dict[str, str]]]:
        layouts = {}
        for mode in enums.EtaType:
            layouts[mode] = [{
                'name': layout['details']['name'],
                'description': layout['details']['description']
            } for layout in cls.layout_data()[mode.value].get('layouts', [])]
        return layouts

    @classmethod
    def layout_data(cls) -> dict[str, dict]:
        """Get the layout configurations of the generator"""
        with open(
            Path(sys.modules[cls.__module__].__file__).with_suffix(".json"),
            "r",
            encoding="utf-8"
        ) as f:
            return json.load(f)

    def __init__(self, eta_type: enums.EtaType, layout_name: str) -> None:
        self.eta_type = eta_type
        self.layout_name = layout_name

        for layout in self.layout_data()[eta_type.value]['layouts']:
            if layout['details']['name'] == layout_name:
                self._config = layout
                self.fonts = FontLoader(layout['fonts'])
                break
        else:
            raise KeyError(layout_name)

    @abstractmethod
    def draw(self,
             etas: Iterable[models.Etas | models.ErrorEta],
             degree: float = 0) -> dict[str, Image.Image]:
        """Create image(s) with the ETA(s) data
        """

    @abstractmethod
    def draw_error(self, message: str, degree: float = 0) -> dict[str, Image.Image]:
        pass

    def write_images(self, directory: os.PathLike, images: dict[str, Image.Image]):
        logging.info(f"saving display output to file(s)")

        if not os.path.exists(directory):
            logging.warn(f"{directory} do not exist, creating...")
            os.makedirs(directory)

        for color, image in images.items():
            eimage.save(os.path.join(directory, f"{color}.bmp"))
            logging.debug(f"{color}.bmp created")

    def read_images(self, directory: os.PathLike) -> dict[str, Image.Image]:
        logging.info(f"reading display output(s) from file(s)")

        images = {}
        for color in self.colors:
            images[color] = Image.open(os.path.join(directory, f"{color}.bmp"))
        return images


class FontLoader(collections.abc.Mapping):

    _cache: dict[str, dict[int, ImageFont.FreeTypeFont]]
    _data: dict[str, ImageFont.FreeTypeFont]

    def __init__(self, font_list: dict[str, dict[str]]) -> None:
        self._cache, self._data = {}, {}
        for key, config in font_list.items():
            self._cache.setdefault(config['font'], {})
            self._cache[config['font']].setdefault(
                config['size'],
                ImageFont.truetype(
                    str(Path(__file__).parent.joinpath(
                        "fonts", config['font'])),
                    config['size'])
            )
            self._data[key] = self._cache[config['font']][config['size']]

    def __getitem__(self, key: str) -> ImageFont.FreeTypeFont:
        return self._data[key]

    def __iter__(self) -> ImageFont.FreeTypeFont:
        for item in self._data.items():
            yield item

    def __len__(self) -> int:
        return len(self._data)


class EtaImageGeneratorFactory:

    @classmethod
    def brands(cls) -> Iterable[str]:
        return ("waveshare",)

    @classmethod
    def models(cls, brand: str) -> Iterable[type[EtaImageGenerator]]:
        try:
            import waveshare
        except ImportError:
            from . import waveshare

        match brand.lower():
            case "waveshare":
                return waveshare.image_cls
        raise KeyError(brand)

    @classmethod
    def get_generator(cls, brand: str, model: str) -> type[EtaImageGenerator]:
        for generator in cls.models(brand):
            if model == generator.__name__:
                return generator
        raise KeyError(model)
