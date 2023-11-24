import json
from collections import abc
from pathlib import Path
import random
import string
from typing import Any, Optional, Self

from pydantic import BaseModel

from app import models, utils
from app.config import flask_config


@utils.singleton
class ApiServerSetting:

    url: Optional[str]
    username: Optional[str]
    password: Optional[str]

    _filepath = Path(flask_config.CONFIG_DIR).joinpath("api_server.json")

    def __init__(self) -> None:
        self.url = self.username = self.password = None

        if not self._filepath.exists():
            self._filepath.parent.mkdir(mode=711, parents=True, exist_ok=True)
            self.persist()
        else:
            with open(self._filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

                self.url = data.get('url')
                self.username = data.get('username')
                self.password = data.get('password')

    def clear(self) -> "ApiServerSetting":
        self.url = self.username = self.password = None
        return self

    def update(self,
               *,
               url: str = None,
               username: str = None,
               password: str = None) -> "ApiServerSetting":
        """Update the setting.

        Only non `None` values will be updated\
            (i.e. supplying `None` will not assign `None` to the setting).

        Args:
            url (str, optional): New url. Defaults to None.
            username (str, optional): New username. Defaults to None.
            password (str, optional): New passoword. Defaults to None.

        Returns:
            ApiServerSetting: The instance itself
        """
        self.url = url or self.url
        self.username = username or self.username
        self.password = password or self.password
        return self

    def to_dict(self) -> dict:
        return {
            'url': self.url,
            'username': self.username,
            'password': self.password
        }

    def persist(self) -> None:
        with open(self._filepath, "w", encoding="utf-8") as f:
            json.dump(
                {
                    'url': self.url,
                    'username': self.username,
                    'password': self.password
                },
                f,
                indent=4
            )


@utils.singleton
class BookmarkList(abc.Sequence):

    _data: list[models.EtaConfig]
    _filepath = Path(flask_config.CONFIG_DIR).joinpath("epa_list.json")

    def __init__(self) -> None:
        self._data = []

        if not self._filepath.exists():
            self.persist()
        else:
            self.load()

    def __getitem__(self, index: int) -> None:
        return self._data[index]

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return self._data.__repr__()

    def create(self, value: models.EtaConfig) -> Self:
        value.id = self._gen_id()
        self._data.append(value)
        return self

    def insert(self, index: int, value: models.EtaConfig) -> Self:
        value.id = self._gen_id()
        self._data.insert(index, value)
        return self

    def pop(self, index: int) -> models.EtaConfig:
        return self._data.pop(index)

    def remove(self, id: str) -> Self:
        del self._data[self.index(id)]
        return self

    def swap(self, src: str, dest: str) -> Self:
        src, dest = self.index(src), self.index(dest)
        self._data[src], self._data[dest] = self._data[dest], self._data[src]
        return self

    def get(self, id: str, default: Any = None) -> models.EtaConfig:
        try:
            return self._data[self.index(id)]
        except ValueError:
            return default

    def index(self, id: str) -> int:
        for idx, entry in enumerate(self._data):
            if entry.id == id:
                return idx
        raise ValueError(f"ETA entry with id '{id}' is not in list.")

    def update(self, id: str, value: models.EtaConfig) -> Self:
        self._data[self.index(id)] = value
        return self

    def load(self) -> None:
        with open(self._filepath, "r", encoding="utf-8") as f:
            self._data = [models.EtaConfig(**c) for c in json.load(f)]

    def persist(self) -> None:
        keys = set([k.id for k in self._data])
        if None in keys:
            raise Exception("Empty ID.")
        if len(keys) != len(self._data):
            raise Exception("Duplicated ID.")

        with open(self._filepath, "w", encoding="utf-8") as f:
            print(self._data)
            json.dump(self._data, f, indent=4, cls=utils.DataclassJSONEncoder)

    def _gen_id(self) -> str:
        return ''.join(random.choice(string.ascii_uppercase + string.digits)
                       for _ in range(6))


@utils.singleton
class EpaperSetting(BaseModel):

    brand: Optional[str]
    model: Optional[str]
    layout: Optional[str]

    _filepath = Path(flask_config.CONFIG_DIR).joinpath("e-paper.json")

    def __init__(self) -> None:
        self.brand = self.model = self.layout = None

        if not self._filepath.exists():
            self._filepath.parent.mkdir(mode=711, parents=True, exist_ok=True)
            self.persist()
        else:
            with open(self._filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

                self.brand = data.get('brand')
                self.model = data.get('model')
                self.layout = data.get('layout')

    def clear(self) -> "EpaperSetting":
        self.brand = self.model = self.layout = None
        return self

    def update(self,
               *,
               brand: str = None,
               model: str = None,
               layout: str = None) -> "EpaperSetting":
        self.brand = brand or self.brand
        self.model = model or self.model
        self.layout = layout or self.layout
        return self

    def persist(self) -> None:
        with open(self._filepath, "w", encoding="utf-8") as f:
            json.dump(
                {
                    'brand': self.brand,
                    'model': self.model,
                    'layout': self.layout
                },
                f,
                indent=4
            )
