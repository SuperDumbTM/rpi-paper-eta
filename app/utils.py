import dataclasses
from enum import Enum
import json
from flask import request, url_for
import pydantic


def singleton(class_):
    instances = {}

    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]
    return getinstance


def redirect_url(default='index'):
    return request.args.get('next') or request.referrer or url_for(default)


def asdict_factory(data):
    """Reference: https://stackoverflow.com/a/64693838"""
    def convert_value(obj):
        if isinstance(obj, Enum):
            return obj.value
        return obj
    return dict((k, convert_value(v)) for k, v in data)


class DataclassJSONEncoder(json.JSONEncoder):
    def default(s, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)
