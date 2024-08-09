import importlib
import sys
from pathlib import Path

from . import controller, waveshare  # DO NOT REMOVE
from .controller import Controller, Partialable


_PATH = Path(__file__).parent


def brands() -> tuple[str]:
    return (b.stem for b in _PATH.glob("[!_]*/"))


def models(brand: str) -> list[type[Controller]]:
    return (m.stem for m in _PATH.joinpath(brand).glob("[!_]*.py"))


def get(brand: str,
        model: str,
        *,
        is_partial: bool
        ) -> Controller:
    module = importlib.import_module(f".{model}",
                                     sys.modules[__name__].__dict__.get(brand).__package__)

    return module.__dict__.get("Controller")(is_partial=is_partial)
