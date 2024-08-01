import json
from pathlib import Path
from typing import Any, Iterator, Mapping

from flask import current_app


class AppConfiguration(Mapping):
    """A Singleton class that mangage all the general configuration including 
        e-paper and API server settings.
    """
    _data: dict[str,]
    _filepath: Path

    __keys__ = ['epd_brand', 'epd_model', 'eta_locale', 'dry_run']

    def __init__(self) -> None:
        self._data = {}
        with current_app.app_context():
            self._filepath = current_app.config['PATH_SITE_CONF']

        if not self._filepath.exists():
            self._filepath.parent.mkdir(mode=711, parents=True, exist_ok=True)
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

    def configurated(self) -> bool:
        return len(self._data) != 0 and all(self.get(k) is not None for k in self.__keys__)

    def _load(self) -> None:
        with open(self._filepath, "r", encoding="utf-8") as f:
            self._data = json.load(f)

    def _persist(self) -> None:
        with open(self._filepath, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=4)
