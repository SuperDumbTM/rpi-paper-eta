import os

try:
    from .enums import Transport
    from .eta_processor import (BravoBusEta, EtaProcessor, KmbEta, MtrBusEta,
                                MtrLrtEta, MtrTrainEta, NlbEta)
    from .models import RouteQuery
    from .route import Route
    from .transport import (CityBus, KowloonMotorBus, MTRBus, MTRLightRail,
                            MTRTrain, NewLantaoBus)
except (ImportError, ModuleNotFoundError):
    from enums import Transport
    from eta_processor import (BravoBusEta, EtaProcessor, KmbEta, MtrBusEta,
                               MtrLrtEta, MtrTrainEta, NlbEta)
    from models import RouteQuery
    from route import Route
    from transport import (CityBus, KowloonMotorBus, MTRBus, MTRLightRail,
                           MTRTrain, NewLantaoBus)


class EtaFactory:

    data_path: os.PathLike

    threshold: int
    """Expiry threshold of the local routes data file"""

    def __init__(self,
                 data_path: os.PathLike = None,
                 threshold: int = 30) -> None:
        self.data_path = data_path
        self.threshold = threshold

    def create_transport(self, transport_: Transport) -> Transport:
        match transport_:
            case Transport.KMB:
                return KowloonMotorBus(self.data_path, self.threshold)
            case Transport.MTRBUS:
                return MTRBus(self.data_path, self.threshold)
            case Transport.MTRLRT:
                return MTRLightRail(self.data_path, self.threshold)
            case Transport.MTRTRAIN:
                return MTRTrain(self.data_path, self.threshold)
            case Transport.CTB:
                return CityBus(self.data_path, self.threshold)
            case Transport.NLB:
                return NewLantaoBus(self.data_path, self.threshold)
            case _:
                raise ValueError(f"Unrecognized transport: {transport_}")

    def create_eta_processor(self, query: RouteQuery) -> EtaProcessor:
        route = self.create_route(query)
        match query.transport:
            case Transport.KMB:
                return KmbEta(route)
            case Transport.MTRBUS:
                return MtrBusEta(route)
            case Transport.MTRLRT:
                return MtrLrtEta(route)
            case Transport.MTRTRAIN:
                return MtrTrainEta(route)
            case Transport.CTB | Transport.NWFB:
                return BravoBusEta(route)
            case Transport.NLB:
                return NlbEta(route)
            case _:
                raise ValueError(f"Unrecognized transport: {query.transport}")

    def create_route(self, query: RouteQuery) -> Route:
        return Route(query, self.create_transport(query.transport))
