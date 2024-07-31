import os

try:
    from .enums import Company
    from .eta_processor import (BravoBusEta, EtaProcessor, KmbEta, MtrBusEta,
                                MtrLrtEta, MtrTrainEta, NlbEta)
    from .models import RouteQuery
    from .route import Route
    from .transport import (CityBus, KowloonMotorBus, MTRBus, MTRLightRail,
                            MTRTrain, NewLantaoBus)
except (ImportError, ModuleNotFoundError):
    from enums import Company
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

    def create_transport(self, transport_: Company) -> Company:
        match transport_:
            case Company.KMB:
                return KowloonMotorBus(self.data_path, self.threshold)
            case Company.MTRBUS:
                return MTRBus(self.data_path, self.threshold)
            case Company.MTRLRT:
                return MTRLightRail(self.data_path, self.threshold)
            case Company.MTRTRAIN:
                return MTRTrain(self.data_path, self.threshold)
            case Company.CTB:
                return CityBus(self.data_path, self.threshold)
            case Company.NLB:
                return NewLantaoBus(self.data_path, self.threshold)
            case _:
                raise ValueError(f"Unrecognized transport: {transport_}")

    def create_eta_processor(self, query: RouteQuery) -> EtaProcessor:
        route = self.create_route(query)
        match query.transport:
            case Company.KMB:
                return KmbEta(route)
            case Company.MTRBUS:
                return MtrBusEta(route)
            case Company.MTRLRT:
                return MtrLrtEta(route)
            case Company.MTRTRAIN:
                return MtrTrainEta(route)
            case Company.CTB | Company.NWFB:
                return BravoBusEta(route)
            case Company.NLB:
                return NlbEta(route)
            case _:
                raise ValueError(f"Unrecognized transport: {query.transport}")

    def create_route(self, query: RouteQuery) -> Route:
        return Route(query, self.create_transport(query.transport))
