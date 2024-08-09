import importlib
import sys
from pathlib import Path
from typing import Iterable, Optional

import PIL.Image

from . import waveshare
from .generator import EtaFormat, ImageRenderer, RendererSpec, Eta

_PATH = Path(__file__).parent


def brands() -> Iterable[str]:
    return (b.stem for b in _PATH.glob("[!_]*/"))


def models(brand: str) -> Iterable[str]:
    return (m.stem for m in _PATH.joinpath(brand).glob("[!_]*/"))


def layouts(brand: str, model: str, format_: str) -> dict[RendererSpec]:
    if brand not in brands() or model not in models(brand):
        raise KeyError(brand)

    specs = {}
    for file in _PATH.joinpath(brand, model, format_).glob("[!_]*.py"):
        module = importlib.import_module(f".{model}.{format_}.{file.stem}",
                                         sys.modules[__name__].__dict__.get(brand).__package__)
        specs[file.stem] = module.__dict__.get("Renderer").spec()
    return specs


def create(brand: str, model: str, format_: str, layout: str) -> ImageRenderer:
    module = importlib.import_module(f".{model}.{format_}.{layout}",
                                     sys.modules[__name__].__dict__.get(brand).__package__)

    return module.__dict__.get("Renderer")()


def render(brand: str, model: str, format_: str, layout: str, etas: Iterable[Eta]):
    return create(brand, model, format_, layout).draw(etas, 0)


def merge(images: dict[str, PIL.Image.Image]) -> Optional[PIL.Image.Image]:
    if len(images) <= 0:
        return None

    if len(images) == 1:
        return images[next(iter(images))]

    for image in images.values():
        merged = PIL.Image.new(
            "RGB", (image.width, image.height), color=(255, 255, 255))
        break

    for rgb, image in images.items():
        image = image.convert("1")
        pixels = image.load()

        for x in range(image.size[0]):
            for y in range(image.size[1]):
                if merged.getpixel((x, y)) != (255, 255, 255):
                    continue
                if pixels[x, y] == 0:
                    merged.putpixel((x, y), tuple(map(int, rgb.split("-"))))
    return merged
