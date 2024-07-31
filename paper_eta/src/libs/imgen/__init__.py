from typing import Iterable

from . import enums, generator, waveshare
from .enums import EtaFormat
from .generator import EtaImageGenerator


def brands() -> Iterable[str]:
    return ("waveshare",)


def models(brand: str) -> Iterable[type[generator.EtaImageGenerator]]:
    match brand.lower():
        case "waveshare":
            return (cls.__name__ for cls in waveshare.MODELS)
    raise KeyError(brand)


def get(brand: str, model: str) -> type[generator.EtaImageGenerator]:
    if brand == "waveshare":
        return getattr(waveshare, model)
    raise KeyError(model)
