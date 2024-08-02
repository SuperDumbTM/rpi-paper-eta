import tomllib

from pathlib import Path
from typing import Iterable

_PATH = Path(__file__).parents[2].joinpath("templates", "epaper")


def brands() -> Iterable[str]:
    return (b.stem for b in _PATH.glob("[!_]*/"))


def models(brand: str) -> Iterable[str]:
    return (b.stem for b in _PATH.joinpath(brand).glob("[!_]*/"))


def layouts(brand: str, model: str):
    if brand not in brands():
        raise KeyError(brand)

    with open(_PATH.joinpath(brand, model, "manifest.toml"), 'rb') as f:
        toml = tomllib.load(f)
        print(toml)


def render(brand: str, model: str):
    pass
