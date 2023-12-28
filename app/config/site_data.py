import json
from collections import abc
from pathlib import Path
from typing import Any, Optional, Self

import croniter
import flask_apscheduler
import requests

from app import config, models, utils
from app.modules import image as eimage


@utils.singleton
class ApiServerSetting:
    """A singleton class for managing the API server setting
    """

    url: Optional[str]
    username: Optional[str]
    password: Optional[str]

    _filepath = Path(config.flask_config.CONFIG_DIR).joinpath(
        "api_server.json")

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
    _filepath = Path(config.flask_config.CONFIG_DIR).joinpath("bookmarks.json")

    def __init__(self) -> None:
        self._data = []
        if not self._filepath.exists():
            self._persist()
        else:
            self._load()

    def __getitem__(self, index: int) -> None:
        return self._data[index]

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return self._data.__repr__()

    def get(self, id: str) -> models.EtaConfig:
        """Return an `EtaConfig` which the id is equal to `id`.
        """
        return self._data[self.index(id)]

    def get_all(self) -> list[models.EtaConfig]:
        """Return all the `EtaConfig`.
        """
        return self._data

    def index(self, id: str) -> int:
        """Return zero-based index in the list of the first item whose id is equal to `id`.

        Args:
            id (str): _description_

        Raises:
            KeyError: No such item with the id equal to `id`.

        Returns:
            int: Index of the matching item.
        """
        for idx, entry in enumerate(self._data):
            if entry.id == id:
                return idx
        raise KeyError(id)

    def create(self, value: models.EtaConfig) -> None:
        self.insert(-1, value)

    def insert(self, index: int, value: models.EtaConfig) -> None:
        while value.id is None or self._is_id_exist(value.id):
            value.id = utils.random_id_gen(6)
        self._data.insert(index, value)
        self._persist()

    def swap(self, id1: str, id2: str) -> None:
        id1, id2 = self.index(id1), self.index(id2)
        self._data[id1], self._data[id2] = self._data[id2], self._data[id1]
        self._persist()

    def update(self, id: str, value: models.EtaConfig) -> Self:
        self._data[self.index(id)] = value
        self._persist()

    def pop(self, index: int) -> models.EtaConfig:
        return self._data.pop(index)

    def remove(self, id: str) -> None:
        del self._data[self.index(id)]
        self._persist()

    def _is_id_exist(self, id: str) -> bool:
        for bm in self._data:
            if bm.id == id:
                return True
        return False

    def _load(self) -> None:
        with open(self._filepath, "r", encoding="utf-8") as f:
            self._data = [models.EtaConfig(**c) for c in json.load(f)]

    def _persist(self) -> None:
        ids = [k.id for k in self._data]

        if len(ids) != len(self._data):
            raise Exception("There exists EtaConfig with no ID.")
        if len(set(ids)) != len(self._data):
            raise KeyError("There exists EtaConfig with duplicated ID.")

        with open(self._filepath, "w", encoding="utf-8") as f:
            json.dump([d.model_dump() for d in self._data], f, indent=4)


@utils.singleton
class EpaperSetting:
    """A Singleton class that mangage the E-Paper settings
    """

    brand: Optional[str]
    model: Optional[str]

    _filepath = Path(config.flask_config.CONFIG_DIR).joinpath("e-paper.json")

    def __init__(self) -> None:
        self.brand = self.model = None

        if not self._filepath.exists():
            self._filepath.parent.mkdir(mode=711, parents=True, exist_ok=True)
            self._persist()
        else:
            self._load()

    def clear(self) -> None:
        self.brand = self.model
        self._persist()

    def update(self,
               *,
               brand: str = None,
               model: str = None) -> None:
        # TODO: update should be automatically presist
        self.brand = brand or self.brand
        self.model = model or self.model
        self._persist()

    def _load(self) -> None:
        with open(self._filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.brand = data.get('brand')
        self.model = data.get('model')

    def _persist(self) -> None:
        with open(self._filepath, "w", encoding="utf-8") as f:
            json.dump(
                {
                    'brand': self.brand,
                    'model': self.model,
                },
                f,
                indent=4
            )


@utils.singleton
class RefreshSchedule:
    """A singleton class for managing the display refresh schedules
    """

    _schedules: list[models.Schedule]
    _filepath = Path(config.flask_config.CONFIG_DIR).joinpath("schedules.json")

    def __init__(self, app) -> None:
        self._schedules = []
        self._aps = flask_apscheduler.APScheduler()
        self._aps.init_app(app)
        self._aps.start()

        if not self._filepath.exists():
            self._filepath.parent.mkdir(mode=711, parents=True, exist_ok=True)
            self._persist()
        else:
            self._load()
            for schedule in self._schedules:
                if not schedule.enabled:
                    continue
                self._add_job(schedule)

    def get(self, id: str) -> models.Schedule:
        for schedule in self._schedules:
            if schedule.id == id:
                return schedule
        raise KeyError(id)

    def get_all(self) -> list[models.Schedule]:
        return self._schedules

    def create(self,
               schedule: str,
               eta_type: str,
               layout: str,
               is_partial: bool,
               enabled: bool) -> str:
        schedule = models.Schedule(
            id=(id := utils.random_id_gen(8)), schedule=schedule, eta_type=eta_type,
            layout=layout, is_partial=is_partial, enabled=enabled)

        if enabled:
            self._add_job(schedule)
        self._schedules.append(schedule)
        self._persist()
        return id

    def update(self,
               id: str,
               schedule: str,
               eta_type: str,
               layout: str,
               is_partial: bool,
               enabled: bool) -> None:
        if not self._is_id_exist(id):
            raise KeyError(id)

        schedule = models.Schedule(
            id=id, schedule=schedule, eta_type=eta_type,
            layout=layout, is_partial=is_partial, enabled=enabled)
        # TODO: optimisa the implementation
        self.remove(id)
        if enabled:
            self._add_job(schedule)
        self._schedules.append(schedule)
        self._persist()

    def remove(self, id: str) -> None:
        for idx, schedule in enumerate(self._schedules):
            if schedule.id == id:
                if self._aps.get_job(id) is not None:
                    self._aps.remove_job(id)
                self._schedules.pop(idx)
                self._persist()
                return
        raise KeyError(id)

    def remove_all(self) -> None:
        self._aps.remove_all_jobs()
        self._schedules.clear()
        self._persist()

    def _load(self) -> None:
        with open(self._filepath, "r", encoding="utf-8") as f:
            self._schedules = [models.Schedule(**c) for c in json.load(f)]

    def _persist(self) -> None:
        with open(self._filepath, "w", encoding="utf-8") as f:
            json.dump([s.model_dump() for s in self._schedules], f, indent=4)

    def _add_job(self, schedule: models.Schedule) -> None:
        if (not croniter.croniter.is_valid(schedule.schedule)):
            raise ValueError('The cron expression is invalid.')

        cron = schedule.schedule.split(' ')
        self._aps.add_job(schedule.id,
                          requests.get,
                          kwargs={
                              'url': 'http://localhost:8002/api/display/refresh',
                              'params': {
                                  'eta_type': eimage.enums.EtaType(schedule.eta_type),
                                  'layout': schedule.layout
                              },
                          },
                          trigger='cron',
                          minute=cron[0],
                          hour=cron[1],
                          day=cron[2],
                          month=cron[3],
                          day_of_week=cron[-1])

    def _is_id_exist(self, id: str) -> bool:
        for schedule in self._schedules:
            if schedule.id == id:
                return True
        return False


@utils.singleton
class RefreshStatus:
    pass
