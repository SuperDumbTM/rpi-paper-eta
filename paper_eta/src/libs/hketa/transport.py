import asyncio
import csv
import io
import json
import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime
from functools import cmp_to_key
from pathlib import Path
from typing import Any, Optional

import aiohttp

try:
    from . import api, enums, exceptions, models
except ImportError:
    import api
    import enums
    import exceptions
    import models


class Transport(ABC):
    """
        Public Transport
        ~~~~~~~~~~~~~~~~~~~~~
        `Transport` representing a public transport company, providing
        information related to the company, mainly operating routes' information

        All child of of `Transport` is implemented as singleton.

        ---
        Language of information returns depends on the `RouteEntry` (if applicatable)

        ---
        Args:
            route_data (RouteData): RouteData instance for `Transport` retriving routes information
    """

    __path_prefix__: Optional[str]

    @property
    @abstractmethod
    def company(self) -> enums.Transport:
        pass

    @property
    def route_list_path(self) -> Path:
        """Path to \"routes\" data file name"""
        return self._root.joinpath('routes.json')

    @property
    def stops_list_dir(self) -> Path:
        """Path to \"route\" data directory"""
        return self._root.joinpath('routes')

    @staticmethod
    def _put_data_file(path: os.PathLike, data) -> None:
        """Write `data` to local file system.
        """
        path = Path(str(path))
        if not path.parent.exists():
            os.makedirs(path.parent)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    'last_update': datetime.now().isoformat(timespec="seconds"),
                    'data': data
                },
                f,
                indent=4
            )

    @staticmethod
    def _route_fname(no: str,
                     direction: enums.Direction,
                     service_type: str) -> str:
        return f"{no.upper()}-{direction.value.lower()}-{service_type.lower()}.json"

    def __init__(self,
                 root: os.PathLike[str] = None,
                 threshold: int = 30) -> None:

        self._root = Path(str(root)).joinpath(self.__path_prefix__)
        if not self._root.exists():
            logging.info("'%s' does not exists, creating...", root)
            os.makedirs(self.stops_list_dir)

        self.threshold = threshold

    def route_list(self) -> dict[str, models.RouteInfo]:
        """Retrive all route list and data operating by the operator.

        Create/update local cache when necessary.
        """
        if self._is_outdated(self.route_list_path):
            routes = asyncio.run(self._fetch_route_list())

            logging.info("%s's route list cache is outdated or not exists, updating...",
                         str(self.company))
            self._put_data_file(self.route_list_path, routes)
        else:
            with open(self.route_list_path, "r", encoding="utf-8") as f:
                routes = json.load(f)['data']

        return {
            route: models.RouteInfo(
                company=self.company,
                route_no=route,
                inbound=[
                    models.RouteInfo.Detail(
                        route_id=rt_type.get('route_id'),
                        service_type=rt_type['service_type'],
                        orig=models.RouteInfo.Stop(
                            stop_id=rt_type['orig']['stop_id'],
                            seq=rt_type['orig']['seq'],
                            name={
                                enums.Locale[locale.upper()]: text for locale, text in rt_type['orig']['name'].items()}
                        ),
                        dest=models.RouteInfo.Stop(
                            stop_id=rt_type['dest']['stop_id'],
                            seq=rt_type['dest']['seq'],
                            name={
                                enums.Locale[locale.upper()]: text for locale, text in rt_type['dest']['name'].items()}
                        ) if rt_type['dest'] else None
                    ) for rt_type in direction['inbound']
                ],
                outbound=[
                    models.RouteInfo.Detail(
                        route_id=rt_type.get('route_id'),
                        service_type=rt_type['service_type'],
                        orig=models.RouteInfo.Stop(
                            stop_id=rt_type['orig']['stop_id'],
                            seq=rt_type['orig']['seq'],
                            name={
                                enums.Locale[locale.upper()]: text for locale, text in rt_type['orig']['name'].items()}
                        ),
                        dest=models.RouteInfo.Stop(
                            stop_id=rt_type['dest']['stop_id'],
                            seq=rt_type['dest']['seq'],
                            name={
                                enums.Locale[locale.upper()]: text for locale, text in rt_type['dest']['name'].items()}
                        )
                    ) for rt_type in direction['outbound']
                ]
            ) for route, direction in routes.items()
        }

    def stop_list(self,
                  route_no: str,
                  direction: enums.Direction,
                  service_type: str) -> tuple[models.RouteInfo.Stop]:
        """Retrive stop list and data of the `route`.

        Create/update local cache when necessary.
        """
        if route_no not in self.route_list().keys():
            raise exceptions.RouteNotExist(route_no)

        fpath = os.path.join(self.stops_list_dir,
                             self._route_fname(route_no, direction, service_type))

        if self._is_outdated(fpath):
            stops = asyncio.run(
                self._fetch_stop_list(route_no, direction, service_type))

            logging.info(
                "%s stop list cache is outdated, updating...", route_no)
            self._put_data_file(
                self.stops_list_dir.joinpath(self._route_fname(route_no, direction, service_type)), stops)
        else:
            with open(fpath, "r", encoding="utf-8") as f:
                stops = json.load(f)['data']

        return tuple(models.RouteInfo.Stop(**stop) for stop in stops)

    @abstractmethod
    async def _fetch_route_list(self) -> dict[str, dict[str, list]]:
        pass

    @abstractmethod
    async def _fetch_stop_list(self,
                               route_no: str,
                               direction: enums.Direction,
                               service_type: str) -> list[dict[str, Any]]:
        pass

    def _is_outdated(self, fpath: os.PathLike) -> bool:
        """Determine whether a data file is outdated.

        Args:
            fpath (str): File path

        Returns:
            bool: `true` if file not exists or outdated
        """
        fpath = Path(str(fpath))
        if fpath.exists():
            with open(fpath, "r", encoding="utf-8") as f:
                lastupd = datetime.fromisoformat(json.load(f)['last_update'])
                return (datetime.now() - lastupd).days > self.threshold
        else:
            return True


class KowloonMotorBus(Transport):
    __path_prefix__ = "kmb"

    _bound_map = {
        'O': enums.Direction.OUTBOUND.value,
        'I': enums.Direction.INBOUND.value,
    }
    """Direction mapping to `hketa.enums.Direction`"""

    @property
    def company(self) -> enums.Transport:
        return enums.Transport.KMB

    async def _fetch_route_list(self) -> dict:
        async def fetch_route_details(session: aiohttp.ClientSession,
                                      stop: dict) -> dict:
            """Fetch the terminal stops details for the `stop`
            """
            direction = self._bound_map[stop['bound']]
            stop_list = (await api.kmb_route_stop_list(
                stop['route'], direction, stop['service_type'], session))['data']

            return {
                'name': stop['route'],
                'direction': direction,
                'details': {
                    'route_id': f"{stop['route']}_{direction}_{stop['service_type']}",
                    'service_type': stop['service_type'],
                    'orig': {
                        'stop_id': stop_list[0]['stop'],
                        'seq': int(stop_list[0]['seq']),
                        'name': {
                            enums.Locale.EN.value: stop.get('orig_en', "N/A"),
                            enums.Locale.TC.value:  stop.get('orig_tc', "未有資料"),
                        }
                    },
                    'dest': {
                        'stop_id': stop_list[-1]['stop'],
                        'seq': int(stop_list[-1]['seq']),
                        'name': {
                            enums.Locale.EN.value: stop.get('dest_en', "N/A"),
                            enums.Locale.TC.value:  stop.get('dest_tc', "未有資料"),
                        }
                    }
                }
            }

        route_list = {}
        async with aiohttp.ClientSession() as session:
            tasks = (fetch_route_details(session, stop)
                     for stop in (await api.kmb_route_list(session))['data'])

            for route in await asyncio.gather(*tasks):
                # route name
                route_list.setdefault(
                    route['name'], {'inbound': [], 'outbound': []})
                # service type
                route_list[route['name']][route['direction']] \
                    .append(route['details'])
        return route_list

    async def _fetch_stop_list(self,
                               route_no: str,
                               direction: enums.Direction,
                               service_type: str) -> dict:
        if route_no not in self.route_list().keys():
            raise exceptions.RouteNotExist(route_no)

        async def fetch_stop_details(session: aiohttp.ClientSession, stop: dict):
            """Fetch `stop_id`, `seq`, `name` of the 'stop'
            """
            dets = (await api.kmb_stop_details(stop['stop'], session))['data']
            return {
                'stop_id': stop['stop'],
                'seq': stop['seq'],
                'name': {
                    enums.Locale.TC.value: dets.get('name_tc'),
                    enums.Locale.EN.value: dets.get('name_en'),
                }
            }

        async with aiohttp.ClientSession() as session:
            stop_list = await api.kmb_route_stop_list(
                route_no, direction.value, service_type, session)

            stops = await asyncio.gather(
                *[fetch_stop_details(session, stop) for stop in stop_list['data']])
        if len(stops) == 0:
            raise exceptions.RouteError(
                f"{route_no}/{direction.value}/{service_type}")
        return stops


class MTRBus(Transport):
    __path_prefix__ = "mtr_bus"

    _bound_map = {
        'O': enums.Direction.OUTBOUND.value,
        'I': enums.Direction.INBOUND.value,
    }
    """Direction mapping to `hketa.enums.Direction`"""

    @property
    def company(self) -> enums.Transport:
        return enums.Transport.MTRBUS

    async def _fetch_route_list(self) -> dict:
        route_list = {}
        apidata = csv.reader(await api.mtr_bus_stop_list())
        next(apidata)  # ignore header line

        for row in apidata:
            # column definition:
            # route, direction, seq, stopID, stopLAT, stopLONG, stopTCName, stopENName
            direction = self._bound_map[row[1]]
            route_list.setdefault(row[0], {'inbound': [], 'outbound': []})

            if row[2] == "1.00" or row[2] == "1":
                # orignal
                route_list[row[0]][direction].append({
                    'stop_id': f"{row[0]}_{direction}_default",
                    'service_type': "default",
                    'orig': {
                        'stop_id': row[3],
                        'seq': int(row[2].strip(".00")),
                        'name': {enums.Locale.EN: row[7], enums.Locale.TC: row[6]}
                    },
                    'dest': {}
                })
            else:
                # destination
                route_list[row[0]][direction][0]['dest'] = {
                    'stop_id': row[3],
                    'seq': int(row[2].strip(".00")),
                    'name': {enums.Locale.EN: row[7], enums.Locale.TC: row[6]}
                }
        return route_list

    async def _fetch_stop_list(self,
                               route_no: str,
                               direction: enums.Direction,
                               service_type: str) -> dict:
        if (service_type != "default"):
            raise exceptions.ServiceTypeNotExist(service_type)

        async with aiohttp.ClientSession() as session:
            apidata = csv.reader(await api.mtr_bus_stop_list(session))

        stops = [stop for stop in apidata
                 if stop[0] == route_no and self._bound_map[stop[1]] == direction]

        if len(stops) == 0:
            raise exceptions.RouteNotExist(route_no)
        return [{
                'stop_id': stop[3],
                'seq': int(stop[2].strip(".00")),
                'name': {enums.Locale.TC: stop[6], enums.Locale.EN: stop[7]}
                } for stop in stops]


class MTRLightRail(Transport):
    __path_prefix__ = 'mtr_lrt'

    _bound_map = {
        '1': enums.Direction.OUTBOUND.value,
        '2': enums.Direction.INBOUND.value
    }
    """Direction mapping to `hketa.enums.Direction`"""

    @property
    def company(self) -> enums.Transport:
        return enums.Transport.MTRLRT

    async def _fetch_route_list(self) -> dict:
        route_list = {}
        apidata = csv.reader(await api.mtr_lrt_route_stop_list())
        next(apidata)  # ignore the header line

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
                        'stop_id': row[3],
                        'seq': row[6],
                        'name': {enums.Locale.EN: row[5], enums.Locale.TC: row[4]}
                    },
                    'dest': {}
                })
            else:
                # destination
                route_list[row[0]][direction][0]['dest'] = {
                    'stop_id': row[3],
                    'seq': row[6],
                    'name': {enums.Locale.EN.value: row[5], enums.Locale.TC.value: row[4]}
                }
        return route_list

    async def _fetch_stop_list(self,
                               route_no: str,
                               direction: enums.Direction,
                               service_type: str) -> dict:
        if (service_type != "default"):
            raise exceptions.ServiceTypeNotExist(service_type)
        if route_no not in self.route_list().keys():
            raise exceptions.RouteNotExist(route_no)

        apidata = csv.reader(await api.mtr_lrt_route_stop_list())
        stops = [stop for stop in apidata
                 if stop[0] == route_no and self._bound_map[stop[1]] == direction]

        if len(stops) == 0:
            raise exceptions.RouteNotExist(route_no)
        return [{'stop_id': stop[3],
                 'seq': int(stop[6].strip('.00')),
                 'name': {enums.Locale.TC.value: stop[4], enums.Locale.EN.value: stop[5]}
                 } for stop in stops]


class MTRTrain(Transport):
    __path_prefix__ = 'mtr_train'

    _bound_map = {
        'DT': enums.Direction.DOWNLINK.value,
        'UT': enums.Direction.UPLINK.value,
    }
    """Direction mapping to `hketa.enums.Direction`"""

    @property
    def company(self) -> enums.Transport:
        return enums.Transport.MTRTRAIN

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
                    'orig': {
                        'stop_id': row[2],
                        'seq': int(row[6].strip(".00")),
                        'name': {enums.Locale.EN.value: row[5], enums.Locale.TC.value: row[4]}
                    },
                    'dest': {}
                })
            else:
                # destination
                route_list[row[0]][direction][0]['dest'] = {
                    'stop_id': row[2],
                    'seq': int(row[6].strip(".00")),
                    'name': {enums.Locale.EN.value: row[5], enums.Locale.TC.value: row[4]}
                }
        return route_list

    async def _fetch_stop_list(self,
                               route_no: str,
                               direction: enums.Direction,
                               service_type: str) -> dict:
        if (service_type != "default"):
            raise exceptions.ServiceTypeNotExist(service_type)
        if route_no not in self.route_list().keys():
            raise exceptions.RouteNotExist(route_no)

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
            raise exceptions.RouteNotExist(route_no)
        return [{'stop_id': stop[2],
                 'seq': int(stop[-1].strip('.00')),
                 'name': {enums.Locale.TC.value: stop[4], enums.Locale.EN.value: stop[5]}
                 } for stop in stops]


class CityBus(Transport):
    __path_prefix__ = 'ctb'

    @property
    def company(self) -> enums.Transport:
        return enums.Transport.CTB

    async def _fetch_route_list(self) -> dict:
        async def fetch_route_details(session: aiohttp.ClientSession,
                                      route: dict) -> dict:
            """Fetch the terminal stops details (all direction) for the `route`
            """
            directions = {
                'inbound': (await api.bravobus_route_stop_list(
                    "ctb", route['route'], "inbound", session))['data'],
                'outbound': (await api.bravobus_route_stop_list(
                    "ctb", route['route'], "outbound", session))['data']
            }

            routes = {route['route']: {'inbound': [], 'outbound': []}}
            for direction, stop_list in directions.items():
                if len(stop_list) == 0:
                    continue

                ends = await asyncio.gather(*[
                    api.bravobus_stop_details(stop_list[0]['stop']),
                    api.bravobus_stop_details(stop_list[-1]['stop'])
                ])

                routes[route['route']][direction] = [{
                    'route_id': f"{route['route']}_{direction}_default",
                    'service_type': "default",
                    'orig': {
                        'stop_id': stop_list[0]['stop'],
                        'seq': stop_list[0]['seq'],
                        'name': {
                            enums.Locale.EN.value: ends[0]['data'].get('name_en', "N/A"),
                            enums.Locale.TC.value:  ends[0]['data'].get('name_tc', "未有資料"),
                        }
                    },
                    'dest': {
                        'stop_id': stop_list[-1]['stop'],
                        'seq': stop_list[-1]['seq'],
                        'name': {
                            enums.Locale.EN.value: ends[-1]['data'].get('name_en', "N/A"),
                            enums.Locale.TC.value:  ends[-1]['data'].get('name_tc', "未有資料"),
                        }
                    }
                }]
            return routes

        async with aiohttp.ClientSession() as session:
            tasks = [fetch_route_details(session, stop) for stop in
                     (await api.bravobus_route_list("ctb", session))['data']]

            # keys()[0] = route name
            return {list(route.keys())[0]: route[list(route.keys())[0]]
                    for route in await asyncio.gather(*tasks)}

    async def _fetch_stop_list(self,
                               route_no: str,
                               direction: enums.Direction,
                               service_type: str) -> dict:
        if (service_type != "default"):
            raise exceptions.ServiceTypeNotExist(service_type)
        if route_no not in self.route_list().keys():
            raise exceptions.RouteNotExist(route_no)

        async def fetch_stop_details(session: aiohttp.ClientSession, stop: dict):
            """Fetch `stop_id`, `seq`, `name` of the 'stop'
            """
            dets = (await api.bravobus_stop_details(stop['stop'], session))['data']
            return {
                'stop_id': stop['stop'],
                'seq': int(stop['seq']),
                'name': {
                    enums.Locale.EN.value: dets.get('name_en', "N/A"),
                    enums.Locale.TC.value: dets.get('name_tc', "未有資料")
                }
            }

        async with aiohttp.ClientSession() as session:
            stop_list = await api.bravobus_route_stop_list(
                "ctb", route_no, direction.value, session)

            stop_list = await asyncio.gather(
                *[fetch_stop_details(session, stop) for stop in stop_list['data']])

            if len(stop_list) == 0:
                raise exceptions.RouteNotExist(route_no)
            return stop_list


class NewLantaoBus(Transport):

    __path_prefix__ = 'nlb'

    @property
    def company(self) -> enums.Transport:
        return enums.Transport.NLB

    async def _fetch_route_list(self) -> dict:
        output = {}

        async def fetch_route_details(route: dict, session: aiohttp.ClientSession):
            """Return the origin and destination details of a route.
            """
            stops = (await api.nlb_route_stop_list(route['routeId'], session))['stops']
            return {
                "route_no": route['routeNo'],
                "route_id": route['routeId'],
                "orig": {
                    "stop_id": stops[0]['stopId'],
                    "seq": 1,
                    "name": {"en": stops[0]['stopName_e'], "tc": stops[0]['stopName_c']}
                },
                "dest": {
                    "stop_id": stops[-1]['stopId'],
                    "seq": len(stops),
                    "name": {"en": stops[-1]['stopName_e'], "tc": stops[-1]['stopName_c']}
                }
            }

        # normal routes usually comes before speical routes
        # need to be sorted by routeId to store the default server_type properly
        async with aiohttp.ClientSession() as s:
            routes = await asyncio.gather(
                *[fetch_route_details(r, s) for r in
                  sorted((await api.nlb_route_list(s))['routes'],
                         key=cmp_to_key(lambda a, b: int(a['routeId']) - int(b['routeId'])))])

        for route in routes:
            route_no = route['route_no']
            output.setdefault(route_no, {'outbound': [], 'inbound': []})

            service_type = '1'
            direction = 'inbound' if len(
                output[route_no]['outbound']) else 'outbound'

            # since the routes already sorted by ID, we can assume that
            # when both the `outbound` and `inbound` have data, it is a special route.
            if all(len(b) for b in output[route_no]):
                _join = {
                    **{'outbound': output[route_no]['outbound']},
                    **{'inbound': output[route_no]['inbound']}
                }
                for bound, parent_rt in _join.items():
                    for r in parent_rt:
                        # special routes usually diff from either orig or dest stop
                        if (r['orig']['name']['en'] == route['orig']['name']['en']
                                or r['dest']['name']['en'] == route['dest']['name']['en']):
                            direction = bound
                            service_type = str(
                                len(output[route_no][direction]) + 1)
                            break
                    else:
                        continue
                    break

            output[route_no][direction].append({
                "route_id": route['route_id'],
                "service_type": service_type,
                "orig": route['orig'],
                "dest": route['dest'],
            })

        return output

    async def _fetch_stop_list(self,
                               route_no: str,
                               direction: enums.Direction,
                               service_type: str) -> list[dict[str, Any]]:
        # TODO: service type checking
        if route_no not in self.route_list().keys():
            raise exceptions.RouteNotExist(route_no)

        if isinstance(direction, str):
            direction = enums.Direction(direction)
        # route ID lookup
        route_id = self.route_list()[route_no] \
            .service_lookup(direction, service_type) \
            .route_id

        return [{
            'stop_id': stop['stopId'],
            'seq': idx,
            'name': {
                enums.Locale.TC.value: stop['stopName_c'],
                enums.Locale.EN.value: stop['stopName_e'],
            }} for idx, stop in enumerate((await api.nlb_route_stop_list(route_id))['stops'],
                                          start=1)
        ]

    def logo(self) -> io.BufferedReader:
        """Get the company logo in bytes"""
        raise NotImplementedError


if __name__ == '__main__':
    c = MTRBus('.')
    c.route_list()
