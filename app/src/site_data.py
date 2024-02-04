import json
from collections import abc, deque
from pathlib import Path
from typing import Any, Iterator

from app.src import models, utils


@utils.singleton
class AppConfiguration(abc.Mapping):
    """A Singleton class that mangage all the general configuration including 
        e-paper and API server settings.
    """
    _data: dict[str,]
    _filepath = Path(__file__).parents[1].joinpath("data", "config.json")

    __keys__ = ['api_url', 'api_username',
                'api_password', 'epd_brand', 'epd_model',]

    def __init__(self) -> None:
        self._data = {k: None for k in self.__keys__}

        if not self._filepath.exists():
            self._filepath.parent.mkdir(mode=711, parents=True, exist_ok=True)
            self._persist()
        else:
            self._load()

    def __getitem__(self, __key: str) -> Any:
        return self._data.__getitem__(__key)

    def __iter__(self) -> Iterator:
        return self._data.__iter__()

    def __len__(self) -> int:
        return self._data.__len__()

    def update(self, key: str, val: Any) -> None:
        if key not in self.__keys__:
            raise KeyError(key)

        self._data[key] = val
        self._persist()

    def updates(self, mapping: dict) -> None:
        if any(k not in self.__keys__ for k in mapping.keys()):
            raise KeyError(set(mapping.keys()) - set(self.__keys__))

        self._data.update(mapping)
        self._persist()

    def _load(self) -> None:
        with open(self._filepath, "r", encoding="utf-8") as f:
            self._data = json.load(f)

    def _persist(self) -> None:
        with open(self._filepath, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=4)


@utils.singleton
class RefreshHistory:
    _data: deque[models.RefreshLog]

    def __init__(self, limit: int = 20) -> None:
        self._data = deque([], limit)
        self.limit = limit

    def put(self, log: models.RefreshLog) -> None:
        self._data.appendleft(log)

    def get(self) -> tuple[models.RefreshLog]:
        return tuple(l for l in self._data)

    def clear(self) -> None:
        self._data.clear()
