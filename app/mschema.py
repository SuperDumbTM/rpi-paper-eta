from marshmallow import Schema, fields, ValidationError


class ApiServer(Schema):
    url = fields.String(required=True)
    username = fields.String()
    password = fields.String()


class EtaOrderChange(Schema):
    source = fields.String(required=True)
    destination = fields.String(required=True)
