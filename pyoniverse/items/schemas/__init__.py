from typing import List

from marshmallow import Schema, fields


class CrawledInfoSchema(Schema):
    spider: str = fields.Str(required=True)
    id: str = fields.Str(required=True)
    url: str = fields.URL(required=True)


class PriceSchema(Schema):
    value: float = fields.Float(required=True)
    currency: int = fields.Integer(required=True)


class ImageSchema(Schema):
    thumb: str = fields.URL(allow_none=True, required=True)
    others: List[str] = fields.List(fields.URL(), required=True)


class EventSchema(Schema):
    brand: int = fields.Integer(required=True)
    id: int = fields.Integer(required=True)
