import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Literal, Union

import pytz

try:
    from . import api
    from .enums import Locale, StopType
    from .models import Eta
    from .route import Route
except (ImportError, ModuleNotFoundError):
    import api
    from enums import Locale, StopType
    from models import Eta
    from route import Route


def _8601str(dt: datetime) -> str:
    """Convert a `datetime` instance to ISO-8601 formatted string."""
    return dt.isoformat(sep='T', timespec='seconds')


class EtaProcessor(ABC):
    """Public Transport ETA Retriver
    ~~~~~~~~~~~~~~~~~~~~~
    Retrive, process and unify the format of ETA(s) data
    """

    @property
    def route(self) -> Route:
        return self._route

    @route.setter
    def route(self, val):
        if not isinstance(val, Route):
            raise TypeError
        self._route = val

    def __init__(self, route: Route) -> None:
        self._route = route

    @abstractmethod
    def etas(self) -> Eta:
        """Return processed ETAs
        """

    def _g_eta(self,
               etas: Union[list[Eta.Time], Eta.Error]) -> Eta:
        return Eta(no=self.route.entry.no,
                   origin=self.route.orig_name(),
                   destination=self.route.dest_name(),
                   stop_name=self.route.stop_name(),
                   locale=self.route.entry.locale,
                   logo=self.route.logo(),
                   etas=etas,
                   timestamp=datetime.now().replace(tzinfo=pytz.timezone('Etc/GMT-8')))

    def _em(self, code: Literal["api-error", "empty", "eos", "ss-effect"]) -> str:
        return {
            "api-error": {
                Locale.EN: "API Error",
                Locale.TC: "API 錯誤",
            },
            "empty": {
                Locale.EN: "No Data",
                Locale.TC: "沒有預報",
            },
            "eos": {
                Locale.EN: "Not in Service",
                Locale.TC: "服務時間已過",
            },
            "ss-effect": {
                Locale.EN: "Special Service in Effect",
                Locale.TC: "特別車務安排",
            },
        }[code][self.route.entry.locale]


class KmbEta(EtaProcessor):

    _locale_map = {Locale.TC: "tc", Locale.EN: "en"}

    def etas(self):
        response = asyncio.run(
            api.kmb_eta(self.route.entry.no, self.route.entry.service_type))

        if len(response) == 0:
            return self._g_eta(Eta.Error(message=self._em("api-error")))
        if response.get('data') is None:
            return self._g_eta(Eta.Error(message=self._em("empty")))

        etas = []
        timestamp = datetime.fromisoformat(response['generated_timestamp'])
        locale = self._locale_map[self.route.entry.locale]

        for stop in response['data']:
            if (stop["seq"] != self.route.stop_seq()
                    or stop["dir"] != self.route.entry.direction[0].upper()):
                continue
            if stop["eta"] is None:
                if stop[f'rmk_en'] == "The final bus has departed from this stop":
                    return self._g_eta(Eta.Error(message=self._em("eos")))
                elif stop[f'rmk_en'] == "":
                    return self._g_eta(Eta.Error(message=self._em("empty")))
                return self._g_eta(Eta.Error(message=stop[f'rmk_{locale}']))

            eta_dt = datetime.fromisoformat(stop["eta"])
            etas.append(Eta.Time(
                destination=stop[f'dest_{locale}'],
                is_arriving=(eta_dt - timestamp).total_seconds() < 30,
                is_scheduled=stop.get(f'rmk_{locale}') in (
                    '原定班次', 'Scheduled Bus'),
                eta=_8601str(eta_dt),
                eta_minute=int((eta_dt - timestamp).total_seconds() / 60),
                remark=stop[f'rmk_{locale}'],
            ))

            if len(etas) == 3:
                #  NOTE: the number of ETA entry form API at the same stop may not be 3 every time.
                #  KMB only provide at most 3 upcoming ETAs
                #  (e.g. N- routes may provide only 2)
                break

        return self._g_eta(etas)


class MtrBusEta(EtaProcessor):

    _locale_map = {Locale.TC: "zh", Locale.EN: "en"}

    def etas(self):
        response = asyncio.run(
            api.mtr_bus_eta(self.route.name(), self._locale_map[self.route.entry.locale]))

        if len(response) == 0:
            return self._g_eta(Eta.Error(message=self._em("api-error")))
        if response["routeStatusRemarkTitle"] is not None:
            if response["routeStatusRemarkTitle"] in ("\u505c\u6b62\u670d\u52d9", "Non-service hours"):
                return self._g_eta(Eta.Error(message=self._em("eos")))
            return self._g_eta(Eta.Error(message=response["routeStatusRemarkTitle"]))

        etas = []
        timestamp = datetime.strptime(response["routeStatusTime"], "%Y/%m/%d %H:%M") \
            .astimezone(pytz.timezone('Asia/Hong_kong'))

        for stop in response["busStop"]:
            if stop["busStopId"] != self.route.entry.stop_id:
                continue

            for eta in stop["bus"]:
                time_ref = "departure" \
                    if self.route.stop_type() == StopType.ORIG \
                    else "arrival"

                if (any(char.isdigit() for char in eta[f'{time_ref}TimeText'])):
                    # eta TimeText has numbers (e.g. 3 分鐘/3 Minutes)
                    eta_sec = int(eta[f'{time_ref}TimeInSecond'])
                    etas.append(Eta.Time(
                        destination=self.route.destination()["name"].get(
                            self.route.entry.locale),
                        is_arriving=False,
                        is_scheduled=eta['busLocation']['longitude'] == 0,
                        eta=_8601str(timestamp + timedelta(seconds=eta_sec)),
                        eta_minute=eta[f'{time_ref}TimeText'].split(" ")[0],
                    ))
                else:
                    etas.append(Eta.Time(
                        destination=self.route.destination()["name"].get(
                            self.route.entry.locale),
                        is_arriving=True,
                        is_scheduled=eta['busLocation']['longitude'] == 0,
                        eta=_8601str(timestamp),
                        eta_minute=0,
                        remark=eta[f'{time_ref}TimeText'],
                    ))
            break

        return self._g_eta(etas)


class MtrLrtEta(EtaProcessor):

    _locale_map = {Locale.TC: "ch", Locale.EN: "en"}

    def etas(self):
        response = asyncio.run(api.mtr_lrt_eta(self.route.entry.stop_id))
        if len(response) == 0 or response.get('status', 0) == 0:
            return self._g_eta(Eta.Error(message=self._em("api-error")))
        if all(platform.get("end_service_status", False)
               for platform in response['platform_list']):
            return self._g_eta(Eta.Error(message=self._em("eos")))

        etas = []
        cnt_stopped = 0
        timestamp = datetime.fromisoformat(response['system_time']) \
            .astimezone(pytz.timezone('Asia/Hong_kong'))
        lang_code = self._locale_map[self.route.entry.locale]

        for platform in response['platform_list']:
            # the platform may ended service
            for eta in platform.get("route_list", []):
                # 751P have no destination and eta
                destination = eta.get(f'dest_{lang_code}')

                if eta['route_no'] != self.route.entry.no:
                    continue
                if eta.get("stop") == 1:
                    cnt_stopped += 1
                    continue
                if destination != self.route.destination()["name"].get(self.route.entry.locale):
                    continue

                # e.g. 3 分鐘 / 即將抵達
                eta_min = eta[f'time_{lang_code}'].split(" ")[0]
                if eta_min.isnumeric():
                    etas.append(Eta.Time(
                        destination=destination,
                        is_arriving=False,
                        is_scheduled=False,
                        eta=_8601str(
                            timestamp + timedelta(minutes=float(eta_min))),
                        eta_minute=int(eta_min),
                        extras={
                            "platform": str(platform['platform_id']),
                            "car_length": eta['train_length']
                        },
                    ))
                else:
                    etas.append(Eta.Time(
                        destination=destination,
                        is_arriving=True,
                        is_scheduled=False,
                        eta=_8601str(timestamp),
                        eta_minute=0,
                        remark=eta_min,
                        extras={
                            "platform": str(platform['platform_id']),
                            "car_length": eta['train_length']
                        }
                    ))

        if len(etas) > 0:
            return self._g_eta(etas)
        if "red_alert_status" in response.keys():
            return self._g_eta(
                Eta.Error(
                    message=response[f"red_alert_message_{self._locale_map[self.route.entry.locale]}"]))
        # if ((len(response['platform_list']) == 1 and cnt_stopped == 1)
        #         or cnt_stopped >= 2):
        if cnt_stopped > 0:
            return self._g_eta(Eta.Error(message=self._em("eos")))


class MtrTrainEta(EtaProcessor):

    _bound_map = {"inbound": "UP", "outbound": "DOWN"}

    def __init__(self, route: Route) -> None:
        super().__init__(route)
        self.linename = self.route.entry.no.split("-")[0]
        self.direction = self._bound_map[self.route.entry.direction]

    def etas(self):
        response = asyncio.run(
            api.mtr_train_eta(self.linename,
                              self.route.entry.stop_id,
                              self.route.entry.locale.value))

        if len(response) == 0:
            return self._g_eta(Eta.Error(message=self._em("api-error")))
        if response.get('status', 0) == 0:
            if "suspended" in response['message']:
                # raise exceptions.StationClosed(response['message'])
                return self._g_eta(Eta.Error(message=response['message']))
            if response.get('url') is not None:
                return self._g_eta(Eta.Error(message=self._em("ss-effect")))
            return self._g_eta(Eta.Error(message=self._em("api-error")))

        if response['data'][f'{self.linename}-{self.route.entry.stop_id}'].get(self.direction) is None:
            return self._g_eta(Eta.Error(message=self._em("empty")))

        etas = []
        timestamp = datetime.fromisoformat(response["curr_time"]).astimezone(
            pytz.timezone('Asia/Hong_kong'))

        etadata = response['data'][f'{self.linename}-{self.route.entry.stop_id}'].get(
            self.direction, [])
        for entry in etadata:
            eta_dt = datetime.fromisoformat(entry["time"]).astimezone(
                pytz.timezone('Asia/Hong_kong'))
            etas.append(Eta.Time(
                destination=(self.route.stop_details(entry['dest'])["name"]
                             .get(self.route.entry.locale)),
                is_arriving=(eta_dt - timestamp).total_seconds() < 90,
                is_scheduled=False,
                eta=_8601str(eta_dt),
                eta_minute=int((eta_dt - timestamp).total_seconds() / 60),
                extras={"platform": entry['plat']}
            ))

        return self._g_eta(etas)


class BravoBusEta(EtaProcessor):

    _locale_map = {Locale.TC: "tc", Locale.EN: "en"}

    def etas(self):
        response = asyncio.run(
            api.bravobus_eta(self.route.entry.transport.value, self.route.entry.stop_id, self.route.entry.no))

        if len(response) == 0 or response.get('data') is None:
            return self._g_eta(Eta.Error(message=self._em("api-error")))
        if len(response['data']) == 0:
            return self._g_eta(Eta.Error(message=self._em("empty")))

        etas = []
        timestamp = datetime.fromisoformat(response['generated_timestamp'])
        lang_code = self._locale_map[self.route.entry.locale]

        for eta in response['data']:
            if eta['dir'] != self.route.entry.direction[0].upper():
                continue
            if eta['eta'] == "":
                # 九巴時段
                etas.append(Eta.Time(
                    destination=eta[f"dest_{lang_code}"],
                    is_arriving=False,
                    is_scheduled=True,
                    eta=None,
                    eta_minute=None,
                    remark=eta[f"rmk_{lang_code}"]
                ))
            else:
                eta_dt = datetime.fromisoformat(eta['eta'])
                etas.append(Eta.Time(
                    destination=eta[f"dest_{lang_code}"],
                    is_arriving=(eta_dt - timestamp).total_seconds() < 60,
                    is_scheduled=False,
                    eta=_8601str(eta_dt),
                    eta_minute=int((eta_dt - timestamp).total_seconds() / 60),
                    remark=eta[f"rmk_{lang_code}"]
                ))

        return self._g_eta(etas)


class NlbEta(EtaProcessor):

    _lang_map = {Locale.TC: 'zh', Locale.EN: 'en', }

    def etas(self):
        response = asyncio.run(
            api.nlb_eta(self.route.id(), self.route.entry.stop_id, self._lang_map[self.route.entry.locale]))

        if len(response) == 0:
            # incorrect parameter will result in a empty json response
            return self._g_eta(Eta.Error(message=self._em("api-error")))
        if not response.get('estimatedArrivals', []):
            return self._g_eta(Eta.Error(message=self._em("empty")))

        etas = []
        timestamp = datetime.now().replace(tzinfo=pytz.timezone('Etc/GMT-8'))

        for eta in response['estimatedArrivals']:
            eta_dt = datetime.fromisoformat(eta['estimatedArrivalTime']) \
                .astimezone(pytz.timezone('Asia/Hong_kong'))

            etas.append(Eta.Time(
                destination=(
                    self.route.destination().name.get(self.route.entry.locale)),
                is_arriving=(eta_dt - timestamp).total_seconds() < 60,
                is_scheduled=not (eta.get('departed') == '1'
                                  and eta.get('noGPS') == '1'),
                eta=_8601str(eta_dt),
                eta_minute=int((eta_dt - timestamp).total_seconds() / 60),
                extras={"route_variant": eta.get('routeVariantName')}
            ))

        return self._g_eta(etas)
