from pydantic.dataclasses import dataclass


@dataclass(slots=True)
class EtaConfig:
    company: str
    name: str
    direction: str
    service_type: str
    stop: str
    lang: str


@dataclass(slots=True)
class EpdConfig:
    brand: str
    model: str
    layout: str
    style: str
