from marshmallow import Schema, fields

from pyoniverse.items import CrawledInfoSchema, ImageSchema


class BrandEventSchema(Schema):
    crawled_info = fields.Nested(CrawledInfoSchema, required=True)
    created_at = fields.Integer(required=True)
    updated_at = fields.Integer(required=True)
    start_at = fields.Integer(required=True)
    end_at = fields.Integer(required=True)
    name = fields.Str(required=True)
    description = fields.Str(required=True, allow_none=True)
    image = fields.Nested(ImageSchema, required=True)
