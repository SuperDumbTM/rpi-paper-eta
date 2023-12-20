import dataclasses
from enum import Enum
import json
import random
import string

import flask


def singleton(class_):
    """A singleton decorator"""
    instances = {}

    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]
    return getinstance


def redirect_url(default='index'):
    return flask.request.args.get('next') or flask.request.referrer or flask.url_for(default)


def asdict_factory(data):
    """
    `dataclass.asdict` factory that supports `Enum` convertion

    Reference: https://stackoverflow.com/a/64693838"""
    def convert_value(obj):
        if isinstance(obj, Enum):
            return obj.value
        return obj
    return dict((k, convert_value(v)) for k, v in data)


def random_id_gen(length: int) -> str:
    """Generate strings composed with uppercase and digits.
    """
    return ''.join(random.choice(string.ascii_uppercase + string.digits)
                   for _ in range(length))


class DataclassJSONEncoder(json.JSONEncoder):
    def default(s, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)
