import dataclasses
import json
from flask import request, url_for


def singleton(class_):
    instances = {}

    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]
    return getinstance


def redirect_url(default='index'):
    return request.args.get('next') or request.referrer or url_for(default)


class DataclassJSONEncoder(json.JSONEncoder):
    def default(s, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)
