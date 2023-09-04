from marshmallow import Schema, fields


class CrawledInfoSchema(Schema):
    spider: str = fields.Str(required=True)
    id: str = fields.Str(required=True)
    url: str = fields.URL(required=True)


class PriceSchema(Schema):
    value: float = fields.Float(required=True)
    currency: int = fields.Integer(required=True, validate=lambda x: x in [1])


class ImageSchema(Schema):
    thumb: str = fields.URL(required=True)
    others: fields.List(fields.URL, required=True)
