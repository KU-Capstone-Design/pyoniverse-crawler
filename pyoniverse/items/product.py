from dataclasses import KW_ONLY, dataclass, field
from typing import List

from pyoniverse.items import CrawledInfoVO, EventVO, ImageVO, ItemVO, PriceVO
from pyoniverse.items.schemas.product import ProductSchema
from pyoniverse.items.utils import get_timestamp


@dataclass(kw_only=True)
class ProductVO(ItemVO):
    """
    created_at, updated_at 은 자동으로 생성됩니다.
    필요한 경우, 직접 입력해도 됩니다.
    """

    crawled_info: CrawledInfoVO = field()
    name: str = field()
    price: PriceVO = field()
    image: ImageVO = field()
    events: List[EventVO] = field(default_factory=list)
    description: str = field(default=None)
    created_at: int = field(default=None)
    updated_at: int = field(default=None)

    def __post_init__(self):
        self.created_at = get_timestamp()
        self.updated_at = get_timestamp()

    @staticmethod
    def get_collection_name():
        return "products"

    @staticmethod
    def get_schema() -> ProductSchema:
        return ProductSchema()
