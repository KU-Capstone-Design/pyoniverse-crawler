from marshmallow import Schema, fields

from pyoniverse.items.schemas import CrawledInfoSchema


class ProductSchema(Schema):
    crawled_info = fields.Nested(CrawledInfoSchema, required=True)
    name = fields.Str(required=True)
    price = fields.Nested("PriceSchema", required=True)
    image = fields.Nested("ImageSchema", required=True)
    events = fields.List(fields.Integer, required=True)
    created_at = fields.Integer(required=True)
    updated_at = fields.Integer(required=True)
