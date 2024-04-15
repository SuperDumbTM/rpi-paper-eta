import typing


class ApiServerForm(typing.NamedTuple):
    """Form inputs for editing the details of the API server.
    """
    url: str = ''
    # Reference: https://stackoverflow.com/a/53107448/17789727
    username: str = ''
    password: str = ''


class EpaperForm(typing.NamedTuple):
    """Form inputs for creating/editing an Epaper display settings.
    """
    epd_brand: str = ''
    epd_model: str = ''
