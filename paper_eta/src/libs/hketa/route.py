from io import BytesIO

try:
    from .enums import Company, Locale, StopType
    from .exceptions import ServiceTypeNotExist, StopNotExist
    from .models import RouteInfo, RouteQuery
    from .transport import MTRTrain, Transport
except (ImportError, ModuleNotFoundError):
    from enums import Company, Locale, StopType
    from exceptions import ServiceTypeNotExist, StopNotExist
    from models import RouteInfo, RouteQuery
    from transport import MTRTrain, Transport

# MTR do not provide complete route name, need manual translation
MTR_TRAIN_NAMES = {
    'AEL': {Locale.TC: "機場快線", Locale.EN: "Airport Express Line"},
    'TCL': {Locale.TC: "東涌線", Locale.EN: "Tung Chung Line"},
    'TML': {Locale.TC: "屯馬線", Locale.EN: "Tuen Ma Line"},
    'TKL': {Locale.TC: "將軍澳線", Locale.EN: "Tseung Kwan O Line"},
    'TKL-TKS': {Locale.TC: "將軍澳線", Locale.EN: "Tseung Kwan O Line"},
    'EAL': {Locale.TC: "東鐵線", Locale.EN: "East Rail Line"},
    'EAL-LMC': {Locale.TC: "東鐵線", Locale.EN: "East Rail Line"},
    'DRL': {Locale.TC: "迪士尼線", Locale.EN: "Disneyland Resort Line"},
    'KTL': {Locale.TC: "觀塘線", Locale.EN: "Kwun Tong Line"},
    'TWL': {Locale.TC: "荃灣線", Locale.EN: "Tsuen Wan Line"},
    'ISL': {Locale.TC: "港島線", Locale.EN: "Island Line"},
    'SIL': {Locale.TC: "南港島線", Locale.EN: "South Island Line"},
}


class Route:
    """
    Public Transport Route
    ~~~~~~~~~~~~~~~~~~~~~
    `Route` provides methods retrive details of a route (e.g. stop name, stop ID etc.)


    ---
    Language of information returns depends on the `RouteEntry` parameter (if applicatable)
    """

    entry: RouteQuery
    provider: Transport
    _stop_list: dict[str, RouteInfo.Stop]

    def __init__(self, entry: RouteQuery, transport_: Transport) -> None:
        self.entry = entry
        self.provider = transport_
        self._stop_list = {
            stop["id"]: stop
            for stop in self.provider.stop_list(entry.no, entry.direction, entry.service_type)
        }

        if (self.entry.stop_id not in self._stop_list.keys()):
            raise StopNotExist(self.entry.stop_id)

    def company(self) -> Company:
        return self.provider.transport

    def company_name(self) -> str:
        """Get the operating company name of the route"""
        return self.provider.transport.text(self.entry.locale)

    def name(self) -> str:
        """Get the route name of the `entry`"""
        if isinstance(self.provider, type(MTRTrain)):
            return MTR_TRAIN_NAMES.get(self.entry.stop_id, self.entry.stop_id)
        return self.entry.no

    def id(self) -> str:
        for service in self.provider.route_list()[self.entry.no][self.entry.direction.value]:
            if service["service_type"] == self.entry.service_type:
                return self.provider.route_list()[self.entry.no][self.entry.direction.value]["route_id"]
        raise ServiceTypeNotExist(self.entry.service_type)

    def stop_seq(self) -> int:
        """Get the stop sequence of the route"""
        return int(self._stop_list[self.entry.stop_id]["seq"])

    def stop_details(self, stop_id: str) -> RouteInfo.Stop:
        return self._stop_list[stop_id]

    def origin(self) -> RouteInfo.Stop:
        return list(self._stop_list.values())[0]

    def destination(self) -> RouteInfo.Stop:
        stop = list(self._stop_list.values())[-1]

        # NOTE: in/outbound of circular routes are NOT its destination
        # NOTE: 705, 706 return "天水圍循環綫"/'TSW Circular' instead of its destination
        if self.entry.transport == Company.MTRLRT and self.entry.no in ("705", "706"):
            return RouteInfo.Stop(stop_id=stop["id"],
                                  seq=stop["seq"],
                                  name={
                                      Locale.EN: "TSW Circular",
                                      Locale.TC: "天水圍循環綫"
            })
        else:
            return stop

    def stop_type(self) -> StopType:
        """Get the stop type of the stop"""
        if self.origin()["id"] == self.entry.stop_id:
            return StopType.ORIG
        if self.destination()["id"] == self.entry.stop_id:
            return StopType.DEST
        return StopType.STOP

    def stop_name(self) -> str:
        """Get the stop name of the route"""
        return self._stop_list[self.entry.stop_id]["name"][self.entry.locale]

    def orig_name(self) -> str:
        return self.origin()["name"][self.entry.locale]

    def dest_name(self) -> str:
        return self.destination()["name"][self.entry.locale]

    def logo(self) -> BytesIO:
        return self.provider.logo
