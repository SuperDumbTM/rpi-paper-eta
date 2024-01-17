import json
from collections import abc, deque
import logging
from pathlib import Path
from typing import Self

import flask_apscheduler
import requests

from app import config, enums, models, utils
from app.modules import image as eimage


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

    def create(self,
               company: enums.EtaCompany,
               route: str,
               direction: enums.RouteDirection,
               service_type: str,
               stop_code: str,
               lang: str) -> None:
        self.insert(
            -1, company=company, route=route, direction=direction,
            service_type=service_type, stop_code=stop_code, lang=lang)

    def insert(self,
               index: int,
               company: enums.EtaCompany,
               route: str,
               direction: enums.RouteDirection,
               service_type: str,
               stop_code: str,
               lang: str) -> None:

        while 'id_' not in locals() or self._is_id_exist(id_):
            id_ = utils.random_id_gen(8)

        self._data.insert(index, models.EtaConfig(id=id_,
                                                  company=company,
                                                  route=route,
                                                  direction=direction,
                                                  service_type=service_type,
                                                  stop_code=stop_code,
                                                  lang=lang
                                                  ))
        self._persist()

    def update(self, id: str, company: enums.EtaCompany,
               route: str,
               direction: enums.RouteDirection,
               service_type: str,
               stop_code: str,
               lang: str) -> Self:
        self._data[self.index(id)] = models.EtaConfig(id=id,
                                                      company=company,
                                                      route=route,
                                                      direction=direction,
                                                      service_type=service_type,
                                                      stop_code=stop_code,
                                                      lang=lang
                                                      )
        self._persist()

    def swap(self, id1: str, id2: str) -> None:
        id1, id2 = self.index(id1), self.index(id2)
        self._data[id1], self._data[id2] = self._data[id2], self._data[id1]
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
class AppConfiguration:
    """A Singleton class that mangage all the general configuration including 
        e-paper and API server settings.
    """
    _data: models.Configuration

    _filepath = Path(config.flask_config.CONFIG_DIR).joinpath("config.json")

    @property
    def confs(self) -> models.Configuration:
        return self._data

    def __init__(self) -> None:
        self._data = models.Configuration()

        if not self._filepath.exists():
            self._filepath.parent.mkdir(mode=711, parents=True, exist_ok=True)
            self._persist()
        else:
            self._load()

    def get(self, attr_name: str) -> models.Configuration:
        return getattr(self._data, attr_name)

    def update(self, new: models.Configuration) -> None:
        self._data = new
        self._persist()

    def _load(self) -> None:
        with open(self._filepath, "r", encoding="utf-8") as f:
            self._data = models.Configuration(**json.load(f))

    def _persist(self) -> None:
        with open(self._filepath, "w", encoding="utf-8") as f:
            f.write(self._data.model_dump_json(indent=4))


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

    def index(self, id: str) -> int:
        for idx, schedule in enumerate(self._schedules):
            if schedule.id == id:
                return idx
        raise KeyError(id)

    def create(self,
               schedule: str,
               eta_type: eimage.enums.EtaType | str,
               layout: str,
               is_partial: bool,
               enabled: bool) -> str:

        while 'id_' not in locals() or self._is_id_exist(id_):
            id_ = utils.random_id_gen(8)

        schedule = models.Schedule(
            id=id_, schedule=schedule, eta_type=eta_type,
            layout=layout, is_partial=is_partial, enabled=enabled)

        if enabled:
            self._add_job(schedule)
        self._schedules.append(schedule)
        self._persist()
        return id_

    def update(self,
               id: str,
               schedule: str,
               eta_type: eimage.enums.EtaType | str,
               layout: str,
               is_partial: bool,
               enabled: bool) -> None:
        if not self._is_id_exist(id):
            raise KeyError(id)

        schedule = models.Schedule(
            id=id, schedule=schedule, eta_type=eta_type,
            layout=layout, is_partial=is_partial, enabled=enabled)
        if enabled:
            self._add_job(schedule)
        else:
            try:
                self._aps.remove_job(id)
            except KeyError:
                logging.exception("Disabling a non exist job. %s", id)

        self._schedules[self.index(id)] = schedule
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
        cron = schedule.schedule.split(' ')
        self._aps.add_job(schedule.id,
                          requests.get,
                          kwargs={
                              'url': 'http://localhost:8002/api/display/refresh',
                              'params': {
                                  'eta_type': eimage.enums.EtaType(schedule.eta_type),
                                  'layout': schedule.layout,
                                  'is_partial': schedule.is_partial
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
