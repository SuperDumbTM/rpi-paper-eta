from collections import abc
import json
from pathlib import Path
from typing import Optional
from app import models, utils

from app.config import flask_config
from app import models


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
class EtaList(abc.MutableSequence):

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

    def __delitem__(self, index: int) -> None:
        del self._data[index]

    def __setitem__(self, index: int, value: models.EtaConfig) -> None:
        self._data[index] = value

    def insert(self, index: int, value: models.EtaConfig):
        self._data.insert(index, value)

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return self._data.__repr__()

    def load(self):
        with open(self._filepath, "r", encoding="utf-8") as f:
            self._data = [models.EtaConfig(**c) for c in json.load(f)]

    def persist(self) -> None:
        with open(self._filepath, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=4, cls=utils.DataclassJSONEncoder)
