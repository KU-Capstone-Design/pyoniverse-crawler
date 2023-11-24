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
    thumb = fields.Nested(ImageSizeSchema, allow_none=True, required=False)
    others = fields.Nested(ImageSizeSchema, allow_none=True, required=False, many=True)


class ImageSchema(Schema):
    thumb: str = fields.URL(
        allow_none=True,
        required=True,
        schemes=["http", "https", "s3"],
        require_tld=False,
    )
    others: List[str] = fields.List(
        fields.URL(required=True, schemes=["http", "https", "s3"], require_tld=False),
        required=True,
    )
    size: dict = fields.Nested(ImageSizeMapSchema, required=True)


class EventSchema(Schema):
    brand: int = fields.Integer(required=True)
    id: int = fields.Integer(required=True)
