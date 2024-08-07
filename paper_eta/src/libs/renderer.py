import json
import logging
import tempfile
from enum import Enum
from pathlib import Path
from typing import Iterable, Literal

import html2image
from flask import Flask, render_template
import PIL.Image

from paper_eta.src.libs import hketa


class EtaFormat(str, Enum):
    MIXED = "mixed"
    RELATIVE = "relative"
    ABSOLUTE = "absolute"


class Renderer:

    app: Flask
    dir_tmp: Path
    dir_template: Path

    def __init__(self, app: Flask = None) -> None:
        self.dir_tmp = Path(tempfile.gettempdir()).joinpath("paper_eta_tmp")
        self.dir_dump = Path(tempfile.gettempdir()).joinpath("paper_eta_dump")
        self.dir_template = Path(__file__)\
            .parents[2]\
            .joinpath("templates", "epaper")

        if app:
            self.init_app(app)

    def init_app(self, app: Flask):
        self.app = app

        self.dir_tmp = Path(app.config.get("DIR_RENDERER_TMP", self.dir_tmp))
        self.dir_dump = Path(app.config.get("DIR_SCREEN_DUMP", self.dir_dump))
        self.dir_template = Path(app.template_folder).joinpath("epaper")

    def brands(self) -> Iterable[str]:
        return (b.stem for b in self.dir_template.glob("[!_]*/"))

    def models(self, brand: str) -> Iterable[str]:
        return (b.stem for b in self.dir_template.joinpath(brand).glob("[!_]*/"))

    def layouts(self, brand: str, model: str, display: Literal["mixed", "relative", "absolute"]):
        if brand not in self.brands():
            raise KeyError(brand)
        return {
            k: v
            for k, v in self.load_manifest(brand, model, display).items() if not k.startswith('_')
        }

    def render(self, brand: str, model: str, display: str, layout: str, etas: Iterable[hketa.Eta]):
        mnf = self.load_manifest(brand, model, display)
        hti = html2image.Html2Image(output_path=self.dir_tmp,
                                    size=(mnf["_config"]["width"] * mnf["_config"]["scale"],
                                          mnf["_config"]["height"] * mnf["_config"]["scale"])
                                    )

        images = {}
        for color, template in mnf[layout]["colors"].items():
            p = hti.screenshot(
                render_template("/".join(("epaper", brand, model, display, template)),
                                etas=etas,
                                config=mnf["_config"],
                                manifest=mnf[layout],
                                scale=mnf["_config"]["scale"]), save_as=f"{color}.png")

            image = PIL.Image.open(p[0]).convert("L")
            pixel = image.load()
            image.putdata([0 if pixel[x, y] != 255 else 255
                           for y in range(image.size[1])
                           for x in range(image.size[0])])
            images[color] = image.convert("1")\
                .resize((mnf["_config"]["width"], mnf["_config"]["height"]))
        return images

    def load_manifest(self,
                      brand: str,
                      model: str,
                      display: Literal["mixed", "relative", "absolute"]) -> dict[str,]:
        with open(
                self.dir_template.absolute().joinpath(brand, model, display, "manifest.json"), 'rb') as f:
            return json.load(f)

    def save(self, images: dict[str, PIL.Image.Image]):
        logging.debug("Saving images...")
        if not self.dir_dump.exists():
            logging.info("%s do not exist, creating...", self.dir_dump)
            self.dir_dump.mkdir()

        for color, image in images.items():
            image.save(self.dir_dump.joinpath(f"{color}.bmp"))
            logging.debug("Created image: %s",
                          self.dir_dump.joinpath(f"{color}.bmp"))

    def load(self) -> dict[str, PIL.Image.Image]:
        images = {}
        for path in self.dir_dump.glob('*'):
            if path.suffix != '.bmp':
                continue
            images.setdefault(path.name.removesuffix(path.suffix),
                              PIL.Image.open(path))
        return images
