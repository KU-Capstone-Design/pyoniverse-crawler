from marshmallow import Schema, fields

from pyoniverse.items.schemas import (
    CrawledInfoSchema,
    EventSchema,
    ImageSchema,
    PriceSchema,
)


class ProductSchema(Schema):
    crawled_info = fields.Nested(CrawledInfoSchema, required=True)
    category = fields.Integer(required=True)
    name = fields.Str(required=True)
    price = fields.Nested(PriceSchema, required=True)
    image = fields.Nested(ImageSchema, required=True)
    events = fields.Nested(EventSchema, many=True, required=True)
    description = fields.Str(allow_none=True)
    created_at = fields.Integer(required=True)
    updated_at = fields.Integer(required=True)
