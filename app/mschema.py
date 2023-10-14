from marshmallow import Schema, fields, ValidationError


class ApiServer(Schema):
    url = fields.String(required=True)
    username = fields.String()
    password = fields.String()


class EtaBookmark(Schema):
    pass
