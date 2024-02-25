import typing

from app.src.libs import image as eimage


class ApiServerForm(typing.NamedTuple):
    """Form inputs for editing the details of the API server.
    """
    url: str = ''
    # Reference: https://stackoverflow.com/a/53107448/17789727
    username: str = ''
    password: str = ''


class BookmarkForm(typing.NamedTuple):
    """Form inputs for creating/editing an ETA bookmarks.
    """
    company: str = ''
    route: str = ''
    direction: str = ''
    service_type: str = ''
    stop_code: str = ''
    lang: str = ''


class EpaperForm(typing.NamedTuple):
    """Form inputs for creating/editing an Epaper display settings.
    """
    epd_brand: str = ''
    epd_model: str = ''


class ScheduleForm(typing.NamedTuple):
    """Form inputs for creating/editing an Display refreshing schedules.
    """
    schedule: str = ''
    eta_type: str = eimage.enums.EtaType.MIXED
    layout: str = ''
    is_partial: bool = False
    enabled: bool = True
