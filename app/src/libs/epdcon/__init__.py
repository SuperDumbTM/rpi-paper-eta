from . import controller, waveshare
from .controller import DisplayController, Partialable

__all__ = [
    controller,
    waveshare,
]


def brands() -> tuple[str]:
    return ("waveshare",)


def models(brand: str) -> list[type[DisplayController]]:
    try:
        import waveshare
    except ImportError:
        from . import waveshare

    match brand:
        case "waveshare":
            return waveshare.epapers
    raise KeyError(f"Unrecognized epaper brand: {brand}")


def get(brand: str,
        model: str,
        *,
        is_partial: bool
        ) -> DisplayController:
    for controller in models(brand):
        if model == controller.__name__:
            return controller(is_partial)
    raise KeyError(f"Unrecognized epaper: {brand}-{model}")
