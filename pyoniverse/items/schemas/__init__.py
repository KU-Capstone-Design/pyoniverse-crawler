from typing import List, Optional

from marshmallow import Schema, fields


class CrawledInfoSchema(Schema):
    spider: str = fields.Str(required=True)
    id: str = fields.Str(required=True)
    url: str = fields.URL(required=True)
    brand: int = fields.Integer(required=True)


class PriceSchema(Schema):
    value: float = fields.Float(required=True)
    currency: int = fields.Integer(required=True)
    discounted_value: Optional[float] = fields.Float(allow_none=True, required=True)


class ImageSizeSchema(Schema):
    width: int = fields.Integer(required=True)
    height: int = fields.Integer(required=True)


class ImageSizeMapSchema(Schema):
    thumb: ImageSizeSchema = fields.Dict(required=True)
    others: List[dict] = fields.Nested(ImageSizeSchema, required=True, many=True)


class ImageSchema(Schema):
    thumb: str = fields.URL(allow_none=True, required=True)
    others: List[str] = fields.List(fields.URL(), required=True)
    size: dict = fields.Nested(ImageSizeMapSchema, required=True)


class EventSchema(Schema):
    brand: int = fields.Integer(required=True)
    id: int = fields.Integer(required=True)
