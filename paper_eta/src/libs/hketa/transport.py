import asyncio
import csv
import io
import json
import logging
import os
from abc import ABC, ABCMeta, abstractmethod
from datetime import datetime
from functools import cmp_to_key
from pathlib import Path
from typing import Iterable, Optional

import aiohttp

try:
    from . import api
    from .enums import Company, Direction, Locale
    from .exceptions import RouteError, RouteNotExist, ServiceTypeNotExist
    from .models import RouteInfo
except (ImportError, ModuleNotFoundError):
    import api
    from enums import Company, Direction, Locale
    from exceptions import RouteError, RouteNotExist, ServiceTypeNotExist
    from models import RouteInfo

_DIR_IMG = os.path.join(os.path.dirname(__file__), 'images', 'bw_neg')


def stop_list_fname(no: str,
                    direction: Direction,
                    service_type: str) -> str:
    """Get the file name of the stop list file.
    """
    return f"{no.upper()}-{direction.value.lower()}-{service_type.lower()}.json"


def _append_timestamp(data: list | dict) -> dict[str,]:
    return {
        'last_update': datetime.now().isoformat(timespec="seconds"),
        'data': data
    }


def _put_data_file(path: os.PathLike, data) -> None:
    """Write `data` to local file system encoded in JSON format.
    """
    path = Path(str(path))
    if not path.parent.exists():
        os.makedirs(path.parent)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


class Transport(ABC):
    """
        Public Transport
        ~~~~~~~~~~~~~~~~~~~~~
        `Transport` representing a public transport company, providing
        information related to the company, mainly operating routes' information

        ---
        Language of information returns depends on the `RouteEntry` (if applicatable)
    """
    __path_prefix__: Optional[str] = None
    _routes: dict[str, RouteInfo] = None

    @property
    def route_list_path(self) -> Path:
        """Path to \"routes\" data file name"""
        return self._root.joinpath('routes.json')

    @property
    def stops_list_dir(self) -> Path:
        """Path to \"route\" data directory"""
        return self._root.joinpath('routes')

    @property
    def logo(self) -> io.BytesIO:
        with open(os.path.join(_DIR_IMG, f'{self.transport.value}.bmp'), 'rb') as b:
            return io.BytesIO(b.read())

    @property
    @abstractmethod
    def transport(self) -> Company:
        pass

    def __init__(self,
                 root: os.PathLike[str] = None,
                 threshold: int = 30) -> None:

        if self.__path_prefix__ is None:
            self.__path_prefix__ = self.__class__.__name__.lower()

        self._root = Path(str(root)).joinpath(self.__path_prefix__)
        if not self._root.exists():
            logging.info("'%s' does not exists, creating...", root)
            os.makedirs(self.stops_list_dir)

        self.threshold = threshold

    def route_list(self) -> dict[str, RouteInfo]:
        """Retrive all route list and data operating by the operator.

        Create/update local cache when necessary.
        """
        if self._routes is None:
            try:
                with open(self.route_list_path, 'r', encoding='UTF-8') as f:
                    self._routes = json.load(f)
            except (FileNotFoundError, PermissionError):
                logging.info("%s's route list cache do not exists, updating...",
                             str(self.transport.value))

                self._routes = _append_timestamp(
                    asyncio.run(self._fetch_route_list()))
                _put_data_file(self.route_list_path, self._routes)

        if self._is_outdated(self._routes):
            logging.info("%s's route list cache is outdated, updating...",
                         str(self.transport.value))

            self._routes = _append_timestamp(
                asyncio.run(self._fetch_route_list()))
            _put_data_file(self.route_list_path, self._routes)

        return self._routes["data"]

    def stop_list(self,
                  route_no: str,
                  direction: Direction,
                  service_type: str) -> tuple[RouteInfo.Stop]:
        """Retrive stop list and data of the `route`.

        Create/update local cache when necessary.
        """
        if route_no not in self.route_list().keys():
            raise RouteNotExist(route_no)

        fpath = os.path.join(self.stops_list_dir,
                             stop_list_fname(route_no, direction, service_type))

        if self._is_outdated(fpath):
            logging.info(
                "%s stop list cache is outdated, updating...", route_no)

            stops = tuple(asyncio.run(
                self._fetch_stop_list(route_no, direction, service_type)))
            _put_data_file(
                self.stops_list_dir.joinpath(stop_list_fname(route_no, direction, service_type)), _append_timestamp(stops))
        else:
            with open(fpath, "r", encoding="utf-8") as f:
                stops = json.load(f)['data']

        return tuple(stops)

    @abstractmethod
    async def _fetch_route_list(self) -> dict[str, RouteInfo]:
        pass

    @abstractmethod
    async def _fetch_stop_list(self,
                               route_no: str,
                               direction: Direction,
                               service_type: str) -> Iterable[RouteInfo.Stop]:
        pass

    def _is_outdated(self, target: str | dict[str, datetime]) -> bool:
        """Determine whether the data is outdated.
        """
        if isinstance(target, str):
            fpath = Path(str(target))
            if fpath.exists():
                with open(fpath, "r", encoding="utf-8") as f:
                    lastupd = datetime.fromisoformat(
                        json.load(f)['last_update'])
            else:
                return True
        else:
            lastupd = datetime.fromisoformat(target['last_update'])
        return (datetime.now() - lastupd).days > self.threshold


class KowloonMotorBus(Transport):
    __path_prefix__ = "kmb"

    _bound_map = {
        'O': Direction.OUTBOUND.value,
        'I': Direction.INBOUND.value,
    }
    """Direction mapping to `hketa.Direction`"""

    @property
    def transport(self) -> Company:
        return Company.KMB

    async def _fetch_route_list(self):
        async def fetch(session: aiohttp.ClientSession,
                        stop: dict) -> tuple[str, str, RouteInfo.Bound]:
            direction = self._bound_map[stop['bound']]
            stop_list = (await api.kmb_route_stop_list(
                stop['route'], direction, stop['service_type'], session))['data']
            return (stop['route'], direction, {
                'route_id': f"{stop['route']}_{direction}_{stop['service_type']}",
                'service_type': stop['service_type'],
                'orig': {
                    'id': stop_list[0]['stop'],
                    'seq': int(stop_list[0]['seq']),
                    'name': {
                        Locale.EN.value: stop.get('orig_en', "N/A"),
                        Locale.TC.value:  stop.get('orig_tc', "未有資料"),
                    }
                },
                'dest': {
                    'id': stop_list[-1]['stop'],
                    'seq': int(stop_list[-1]['seq']),
                    'name': {
                        Locale.EN.value: stop.get('dest_en', "N/A"),
                        Locale.TC.value:  stop.get('dest_tc', "未有資料"),
                    }
                }
            })

        route_list = {}
        async with aiohttp.ClientSession() as session:
            tasks = (fetch(session, stop) for stop in (await api.kmb_route_list(session))['data'])
            for route in await asyncio.gather(*tasks):
                route_list.setdefault(
                    route[0], RouteInfo(inbound=[], outbound=[]))
                route_list[route[0]][route[1]].append(route[2])
        return route_list

    async def _fetch_stop_list(self,
                               route_no: str,
                               direction: Direction,
                               service_type: str):
        if route_no not in self.route_list().keys():
            raise RouteNotExist(route_no)

        async def fetch(session: aiohttp.ClientSession, stop: dict):
            dets = (await api.kmb_stop_details(stop['stop'], session))['data']
            return RouteInfo.Stop(
                id=stop['stop'],
                seq=stop['seq'],
                name={
                    Locale.TC.value: dets.get('name_tc'),
                    Locale.EN.value: dets.get('name_en'),
                }
            )

        async with aiohttp.ClientSession() as session:
            stop_list = await api.kmb_route_stop_list(
                route_no, direction.value, service_type, session)

            stops = await asyncio.gather(
                *[fetch(session, stop) for stop in stop_list['data']])
        if len(stops) == 0:
            raise RouteError(f"{route_no}/{direction.value}/{service_type}")
        return stops


class MTRBus(Transport):
    __path_prefix__ = "mtr_bus"

    _bound_map = {
        'O': Direction.OUTBOUND.value,
        'I': Direction.INBOUND.value,
    }
    """Direction mapping to `hketa.Direction`"""

    @property
    def transport(self) -> Company:
        return Company.MTRBUS

    async def _fetch_route_list(self):
        route_list: dict[str, RouteInfo] = {}
        next(apidata := csv.reader(await api.mtr_bus_stop_list()))

        for row in apidata:
            # column definition:
            # route, direction, seq, stopID, stopLAT, stopLONG, stopTCName, stopENName
            direction = self._bound_map[row[1]]
            route_list.setdefault(row[0], RouteInfo(inbound=[], outbound=[]))

            if row[2] == "1.00" or row[2] == "1":
                # orignal
                route_list[row[0]][direction].append({
                    'route_id': f"{row[0]}_{direction}_default",
                    'service_type': "default",
                    'orig': RouteInfo.Stop(
                        id=row[3],
                        seq=int(row[2].strip(".00")),
                        name={Locale.EN: row[7], Locale.TC: row[6]}
                    ),
                    'dest': {}
                })
            else:
                # destination
                route_list[row[0]][direction][0]['dest'] = RouteInfo.Stop(
                    id=row[3],
                    seq=int(row[2].strip(".00")),
                    name={Locale.EN: row[7], Locale.TC: row[6]}
                )
        return route_list

    async def _fetch_stop_list(self,
                               route_no: str,
                               direction: Direction,
                               service_type: str) -> dict:
        if (service_type != "default"):
            raise ServiceTypeNotExist(service_type)

        stops = [stop for stop in csv.reader(await api.mtr_bus_stop_list())
                 if stop[0] == route_no and self._bound_map[stop[1]] == direction]

        if len(stops) == 0:
            raise RouteNotExist(route_no)
        return (RouteInfo.Stop(
                id=stop[3],
                seq=int(stop[2].strip(".00")),
                name={Locale.TC: stop[6], Locale.EN: stop[7]}
                ) for stop in stops)


class MTRLightRail(Transport):
    __path_prefix__ = 'mtr_lrt'

    _bound_map = {
        '1': Direction.OUTBOUND.value,
        '2': Direction.INBOUND.value
    }
    """Direction mapping to `hketa.Direction`"""

    @property
    def transport(self) -> Company:
        return Company.MTRLRT

    async def _fetch_route_list(self) -> dict:
        route_list = {}
        next(apidata := csv.reader(await api.mtr_lrt_route_stop_list()))

        for row in apidata:
            # column definition:
            # route, direction , stopCode, stopID, stopTCName, stopENName, seq
            direction = self._bound_map[row[1]]
            route_list.setdefault(row[0], {'inbound': [], 'outbound': []})

            if (row[6] == "1.00"):
                # original
                route_list[row[0]][direction].append({
                    'route_id': f"{row[0]}_{direction}_default",
                    'service_type': "default",
                    'orig': {
                        'id': row[3],
                        'seq': row[6],
                        'name': {Locale.EN: row[5], Locale.TC: row[4]}
                    },
                    'dest': {}
                })
            else:
                # destination
                route_list[row[0]][direction][0]['dest'] = {
                    'id': row[3],
                    'seq': row[6],
                    'name': {Locale.EN.value: row[5], Locale.TC.value: row[4]}
                }
        return route_list

    async def _fetch_stop_list(self,
                               route_no: str,
                               direction: Direction,
                               service_type: str):
        if (service_type != "default"):
            raise ServiceTypeNotExist(service_type)
        if route_no not in self.route_list().keys():
            raise RouteNotExist(route_no)

        stops = [stop for stop in csv.reader(await api.mtr_lrt_route_stop_list())
                 if stop[0] == route_no and self._bound_map[stop[1]] == direction]

        if len(stops) == 0:
            raise RouteNotExist(route_no)
        return (RouteInfo.Stop(
            id=stop[3],
            seq=int(stop[6].strip('.00')),
            name={Locale.TC.value: stop[4], Locale.EN.value: stop[5]}
        ) for stop in stops)


class MTRTrain(Transport):
    __path_prefix__ = 'mtr_train'

    _bound_map = {
        'DT': Direction.DOWNLINK.value,
        'UT': Direction.UPLINK.value,
    }
    """Direction mapping to `hketa.Direction`"""

    @property
    def transport(self) -> Company:
        return Company.MTRTRAIN

    async def _fetch_route_list(self) -> dict:
        route_list = {}
        apidata = csv.reader(await api.mtr_train_route_stop_list())
        next(apidata)  # ignore header line

        for row in apidata:
            # column definition:
            # Line Code, Direction, Station Code, Station ID, Chinese Name, English Name, Sequence
            if not any(row):  # skip empty row
                continue

            direction, _, rt_type = row[1].partition("-")
            if rt_type:
                # route with multiple origin/destination
                direction, rt_type = rt_type, direction  # e.g. LMC-DT
                # make a "new line" for these type of route
                row[0] += f"-{rt_type}"
            direction = self._bound_map[direction]
            route_list.setdefault(row[0], {'inbound': [], 'outbound': []})

            if (row[6] == "1.00"):
                # origin
                route_list[row[0]][direction].append({
                    'route_id': f"{row[0]}_{direction}_default",
                    'service_type': "default",
                    'orig': RouteInfo.Stop(
                        id=row[2],
                        seq=int(row[6].strip(".00")),
                        name={Locale.EN.value: row[5], Locale.TC.value: row[4]}
                    ),
                    'dest': {}
                })
            else:
                # destination
                route_list[row[0]][direction][0]['dest'] = RouteInfo.Stop(
                    id=row[2],
                    seq=int(row[6].strip(".00")),
                    name={Locale.EN.value: row[5], Locale.TC.value: row[4]}
                )
        return route_list

    async def _fetch_stop_list(self,
                               route_no: str,
                               direction: Direction,
                               service_type: str) -> dict:
        if (service_type != "default"):
            raise ServiceTypeNotExist(service_type)
        if route_no not in self.route_list().keys():
            raise RouteNotExist(route_no)

        apidata = csv.reader(await api.mtr_train_route_stop_list())
        if "-" in route_no:
            # route with multiple origin/destination (e.g. EAL-LMC)
            rt_name, rt_type = route_no.split("-")
            stops = [stop for stop in apidata
                     if stop[0] == rt_name and rt_type in stop[1]]
        else:
            stops = [stop for stop in apidata
                     if stop[0] == route_no
                     and self._bound_map[stop[1].split("-")[-1]] == direction]
            # stop[1] (direction) could contain not just the direction (e.g. LMC-DT)

        if len(stops) == 0:
            raise RouteNotExist(route_no)
        return (RouteInfo.Stop(
            id=stop[2],
            seq=int(stop[-1].strip('.00')),
            name={Locale.TC.value: stop[4], Locale.EN.value: stop[5]}
        ) for stop in stops)


class CityBus(Transport):
    __path_prefix__ = 'ctb'

    @property
    def transport(self) -> Company:
        return Company.CTB

    async def _fetch_route_list(self):
        # Stop ID of the same stop from different route will have the same ID,
        # caching the stop details to reduce the number of requests (around 600 - 700).
        # Execution time is not guaranteed to be reduced.
        stop_cache = {}

        async def fetch(session: aiohttp.ClientSession, route: dict):
            directions = {
                'inbound': (await api.bravobus_route_stop_list(
                    "ctb", route['route'], "inbound", session))['data'],
                'outbound': (await api.bravobus_route_stop_list(
                    "ctb", route['route'], "outbound", session))['data']
            }

            info = RouteInfo(inbound=[], outbound=[])
            for direction, stop_list in directions.items():
                if len(stop_list) == 0:
                    continue

                stop_orig = (stop_cache.get(stop_list[0]['stop'])
                             or (await api.bravobus_stop_details(stop_list[0]['stop'], session))['data'])
                stop_cache.setdefault(stop_list[0]['stop'], stop_orig)

                stop_dest = (stop_cache.get(stop_list[-1]['stop'])
                             or (await api.bravobus_stop_details(stop_list[0]['stop'], session))['data'])
                stop_cache.setdefault(stop_list[-1]['stop'], stop_dest)

                info[direction] = [RouteInfo.Bound(
                    route_id=f"{route['route']}_{direction}_default",
                    service_type="default",
                    orig={
                        'id': stop_list[0]['stop'],
                        'seq': stop_list[0]['seq'],
                        'name': {
                            Locale.EN.value: stop_orig.get('name_en', "N/A"),
                            Locale.TC.value:  stop_orig.get('name_tc', "未有資料"),
                        }
                    },
                    dest={
                        'id': stop_list[-1]['stop'],
                        'seq': stop_list[-1]['seq'],
                        'name': {
                            Locale.EN.value: stop_dest.get('name_en', "N/A"),
                            Locale.TC.value:  stop_dest.get('name_tc', "未有資料"),
                        }
                    }
                )]
            return (route['route'], info)

        async with aiohttp.ClientSession() as session:
            tasks = [fetch(session, stop) for stop in
                     (await api.bravobus_route_list("ctb", session))['data']]

            # keys()[0] = route name
            return {route[0]: route[1] for route in await asyncio.gather(*tasks)}

    async def _fetch_stop_list(self,
                               route_no: str,
                               direction: Direction,
                               service_type: str):
        if (service_type != "default"):
            raise ServiceTypeNotExist(service_type)
        if route_no not in self.route_list().keys():
            raise RouteNotExist(route_no)

        async def fetch(session: aiohttp.ClientSession, stop: dict):
            dets = (await api.bravobus_stop_details(stop['stop'], session))['data']
            return RouteInfo.Stop(
                id=stop['stop'],
                seq=int(stop['seq']),
                name={
                    Locale.EN.value: dets.get('name_en', "N/A"),
                    Locale.TC.value: dets.get('name_tc', "未有資料")
                }
            )

        async with aiohttp.ClientSession() as session:
            stop_list = await asyncio.gather(
                *[fetch(session, stop) for stop in
                  (await api.bravobus_route_stop_list("ctb",
                                                      route_no,
                                                      direction.value,
                                                      session)
                   )['data']]
            )

            if len(stop_list) == 0:
                raise RouteNotExist(route_no)
            return stop_list


class NewLantaoBus(Transport):

    __path_prefix__ = 'nlb'

    @property
    def transport(self) -> Company:
        return Company.NLB

    async def _fetch_route_list(self):
        async def fetch(route: dict, session: aiohttp.ClientSession):
            stops = (await api.nlb_route_stop_list(route['routeId'], session))['stops']
            return (route['routeNo'], {
                "route_id": route['routeId'],
                "orig": {
                    "id": stops[0]['stopId'],
                    "seq": 1,
                    "name": {"en": stops[0]['stopName_e'], "tc": stops[0]['stopName_c']}
                },
                "dest": {
                    "id": stops[-1]['stopId'],
                    "seq": len(stops),
                    "name": {"en": stops[-1]['stopName_e'], "tc": stops[-1]['stopName_c']}
                }
            })

        # sort to ensure normal service comes before special service
        # (id of normal services is usually smaller than special service)
        async with aiohttp.ClientSession() as s:
            routes = await asyncio.gather(
                *[fetch(r, s) for r in
                  sorted((await api.nlb_route_list(s))['routes'],
                         key=cmp_to_key(lambda a, b: int(a['routeId']) - int(b['routeId'])))
                  ]
            )

        route_list = {}
        for route in routes:
            route_list.setdefault(route[0], {'outbound': [], 'inbound': []})

            service_type = '1'
            direction = 'inbound' if len(
                route_list[route[0]]['outbound']) else 'outbound'

            # since the routes already sorted by ID, we can assume that
            # when both the `outbound` and `inbound` have data, it is a special route.
            if all(len(b) for b in route_list[route[0]]):
                _join = {
                    **{'outbound': route_list[route[0]]['outbound']},
                    **{'inbound': route_list[route[0]]['inbound']}
                }
                for bound, parent_rt in _join.items():
                    for r in parent_rt:
                        # special routes usually only differ from either orig or dest stop
                        if (r['orig']['name']['en'] == route[1]['orig']['name']['en']
                                or r['dest']['name']['en'] == route[1]['dest']['name']['en']):
                            direction = bound
                            service_type = str(
                                len(route_list[route[0]][direction]) + 1)
                            break
                    else:
                        continue
                    break

            route_list[route[0]][direction].append(RouteInfo.Bound(
                service_type=service_type,
                **route[1]
            ))

        return route_list

    async def _fetch_stop_list(self,
                               route_no: str,
                               direction: Direction,
                               service_type: str):

        if route_no not in self.route_list().keys():
            raise RouteNotExist(route_no)

        for service in self.route_list()[route_no][direction]:
            if service["service_type"] == service_type:
                id_ = service['route_id']
                break
        else:
            raise ServiceTypeNotExist(service_type)

        return (RouteInfo.Stop(
            id=stop['stopId'],
            seq=idx,
            name={
                Locale.TC.value: stop['stopName_c'],
                Locale.EN.value: stop['stopName_e'],
            }) for idx, stop in enumerate((await api.nlb_route_stop_list(id_))['stops'],
                                          start=1)
        )
