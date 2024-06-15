import logging

from flask_babel import gettext, gettext


class HketaException(Exception):
    """Base exception of HketaException"""

    def __init__(self, *args: object) -> None:
        logging.debug("Error occurs: %s", self.__class__.__name__)
        super().__init__(*args)

    @classmethod
    def message(cls) -> str:
        return gettext("Error Occurred")


class EndOfService(HketaException):
    """The service of the route is ended"""

    @classmethod
    def message(cls) -> str:
        return gettext("End of Service")


class ErrorReturns(HketaException):
    """API returned an error with messages//API call failed with messages"""

    @classmethod
    def message(cls) -> str:
        return str(cls)


class APIError(HketaException):
    """API returned an error/API call failed/invalid API returns"""

    @classmethod
    def message(cls) -> str:
        return gettext("API Error")


class EmptyEta(HketaException):
    """No ETA data is/can be provided"""

    @classmethod
    def message(cls) -> str:
        return gettext("No Data")


class StationClosed(HketaException):
    """The station is closed"""

    @classmethod
    def message(cls) -> str:
        return gettext("Station Closed")


class AbnormalService(HketaException):
    """Special service arrangement is in effect"""

    @classmethod
    def message(cls) -> str:
        return gettext("Special Service in Effect")


class RouteError(HketaException):
    """Invalid route"""

    @classmethod
    def message(cls) -> str:
        return gettext("Invalid Route")


class RouteNotExist(RouteError):
    """Invalid route name/number"""

    @classmethod
    def message(cls) -> str:
        return gettext("Invalid Route Number")


class StopNotExist(RouteError):
    """Invalid stop code/ Stop not exists"""

    @classmethod
    def message(cls) -> str:
        return gettext("Invalid Stop")


class ServiceTypeNotExist(RouteError):
    """Invalid srervice type"""

    @classmethod
    def message(cls) -> str:
        return gettext("Invalid Service Type")
