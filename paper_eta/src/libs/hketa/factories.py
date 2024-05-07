import os

try:
    from . import enums, eta_processor, models, transport
    from .route import Route
except (ImportError, ModuleNotFoundError):
    import enums
    import eta_processor
    import models
    import transport
    from route import Route


class EtaFactory:

    data_path: os.PathLike

    threshold: int
    """Expiry threshold of the local routes data file"""

    def __init__(self,
                 data_path: os.PathLike = None,
                 threshold: int = 30) -> None:
        self.data_path = data_path
        self.threshold = threshold

    def create_transport(self, transport_: enums.Transport) -> transport.Transport:
        match transport_:
            case enums.Transport.KMB:
                return transport.KowloonMotorBus(self.data_path, self.threshold)
            case enums.Transport.MTRBUS:
                return transport.MTRBus(self.data_path, self.threshold)
            case enums.Transport.MTRLRT:
                return transport.MTRLightRail(self.data_path, self.threshold)
            case enums.Transport.MTRTRAIN:
                return transport.MTRTrain(self.data_path, self.threshold)
            case enums.Transport.CTB:
                return transport.CityBus(self.data_path, self.threshold)
            case enums.Transport.NLB:
                return transport.NewLantaoBus(self.data_path, self.threshold)
            case _:
                raise ValueError(f"Unrecognized transport: {transport_}")

    def create_eta_processor(self, query: models.RouteQuery) -> eta_processor.EtaProcessor:
        route = self.create_route(query)
        match query.transport:
            case enums.Transport.KMB:
                return eta_processor.KmbEta(route)
            case enums.Transport.MTRBUS:
                return eta_processor.MtrBusEta(route)
            case enums.Transport.MTRLRT:
                return eta_processor.MtrLrtEta(route)
            case enums.Transport.MTRTRAIN:
                return eta_processor.MtrTrainEta(route)
            case enums.Transport.CTB | enums.Transport.NWFB:
                return eta_processor.BravoBusEta(route)
            case enums.Transport.NLB:
                return eta_processor.NlbEta(route)
            case _:
                raise ValueError(f"Unrecognized transport: {query.transport}")

    def create_route(self, query: models.RouteQuery) -> Route:
        return Route(query, self.create_transport(query.transport))
