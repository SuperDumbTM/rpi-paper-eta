import importlib
import sys
from pathlib import Path
from typing import Iterable

from . import waveshare
from .generator import EtaFormat, ImageRenderer, RendererSpec, Eta

_PATH = Path(__file__).parent


def brands() -> Iterable[str]:
    return (b.stem for b in _PATH.glob("[!_]*/"))


def models(brand: str) -> Iterable[str]:
    return (m.stem for m in _PATH.joinpath(brand).glob("[!_]*/"))


def layouts(brand: str, model: str, format: str) -> dict[RendererSpec]:
    if brand not in brands() or model not in models(brand):
        raise KeyError(brand)

    specs = {}
    for file in _PATH.joinpath(brand, model, format).glob("[!_]*.py"):
        module = importlib.import_module(f".{model}.{format}.{file.stem}",
                                         sys.modules[__name__].__dict__.get(brand).__package__)
        specs[file.stem] = module.__dict__.get("Renderer").spec()
    return specs


def render(brand: str, model: str, format: str, layout: str, etas: Iterable[Eta]):
    module = importlib.import_module(f".{model}.{format}.{layout}",
                                     sys.modules[__name__].__dict__.get(brand).__package__)

    renderer: ImageRenderer = module.__dict__.get("Renderer")()
    return renderer.draw(etas, 0)
