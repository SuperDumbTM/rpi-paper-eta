import logging

from . import enums


class HketaException(Exception):
    """Base exception of HketaException"""

    def __init__(self, *args: object) -> None:
        logging.debug("Error occurs: %s", self.__class__.__name__)
        super().__init__(*args)

    @classmethod
    def message(cls, locale: enums.Locale) -> str:
        if locale == enums.Locale.EN:
            return "Error Occurred"
        return "發生未知的錯誤"


class EndOfService(HketaException):
    """The service of the route is ended"""

    @classmethod
    def message(cls, locale: enums.Locale) -> str:
        if locale == enums.Locale.EN:
            return "End of Service"
        return "非服務時間"


class ErrorReturns(HketaException):
    """API returned an error with messages//API call failed with messages"""

    @classmethod
    def message(cls, locale: enums.Locale) -> str:
        return str(cls)


class APIError(HketaException):
    """API returned an error/API call failed/invalid API returns"""

    @classmethod
    def message(cls, locale: enums.Locale) -> str:
        if locale == enums.Locale.EN:
            return "API Error"
        return "API 錯誤"


class EmptyEta(HketaException):
    """No ETA data is/can be provided"""

    @classmethod
    def message(cls, locale: enums.Locale) -> str:
        if locale == enums.Locale.EN:
            return "No Data"
        return "沒有數據"


class StationClosed(HketaException):
    """The station is closed"""

    @classmethod
    def message(cls, locale: enums.Locale) -> str:
        if locale == enums.Locale.EN:
            return "Station Closed"
        return "車站已關閉"


class AbnormalService(HketaException):
    """Special service arrangement is in effect"""

    @classmethod
    def message(cls, locale: enums.Locale) -> str:
        if locale == enums.Locale.EN:
            return "Special Service in Effect"
        return "特別車務安排實施中"


class RouteError(HketaException):
    """Invalid route"""

    @classmethod
    def message(cls, locale: enums.Locale) -> str:
        if locale == enums.Locale.EN:
            return "Invalid Route"
        return "路線不存在"


class RouteNotExist(RouteError):
    """Invalid route name/number"""

    @classmethod
    def message(cls, locale: enums.Locale) -> str:
        if locale == enums.Locale.EN:
            return "Invalid Route Number"
        return "路線編號不存在"


class StopNotExist(RouteError):
    """Invalid stop code/ Stop not exists"""

    @classmethod
    def message(cls, locale: enums.Locale) -> str:
        if locale == enums.Locale.EN:
            return "Invalid Stop"
        return "車站不存在"


class ServiceTypeNotExist(RouteError):
    """Invalid srervice type"""

    @classmethod
    def message(cls, locale: enums.Locale) -> str:
        if locale == enums.Locale.EN:
            return "Invalid Service Type"
        return "班次類別存在"
