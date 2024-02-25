import json
from collections import abc, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Generator, Iterator, Optional

import pydantic
from flask_babel import lazy_gettext

from app.src import utils
from app.src.libs import eta_img


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

    class Log(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

        timestamp: datetime = pydantic.Field(
            default_factory=datetime.now)
        eta_type: eta_img.enums.EtaType
        layout: str
        is_partial: bool
        error: Optional[BaseException] = None

        def model_dump_i18n(self) -> dict:
            return self.model_dump() | {'eta_type': lazy_gettext(self.eta_type.value)}

    _data: deque[Log]
    _limit: int

    @property
    def queue_size(self):
        return self._limit

    @queue_size.setter
    def queue_size(self, val: int):
        if not isinstance(val, int):
            raise TypeError('queue_size can only be assigned to integers.')
        if val <= 0:
            raise ValueError('queue_size must be larger than 0.')
        self._data = deque(self._data, val)

    def __init__(self) -> None:
        self._data = deque([], 60)
        self._limit = 60

    def put(self, log: Log) -> None:
        self._data.appendleft(log)

    def get(self) -> Generator[Log, None, None]:
        return (l for l in self._data)

    def clear(self) -> None:
        self._data.clear()
