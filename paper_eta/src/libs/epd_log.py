from collections import deque
from datetime import datetime
from typing import Generator, Optional

import pydantic
from flask_babel import lazy_gettext

from . import eta_img


class Log(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

    eta_format: eta_img.enums.EtaFormat
    layout: str
    is_partial: bool
    timestamp: datetime = pydantic.Field(default_factory=datetime.now)
    remark: str = ""
    error: Optional[BaseException] = None

    def model_dump_i18n(self) -> dict:
        return self.model_dump() | {'eta_format': lazy_gettext(self.eta_format.value)}


class EpdLog:

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


epdlog = EpdLog()
