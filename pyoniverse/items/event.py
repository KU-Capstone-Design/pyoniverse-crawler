from dataclasses import dataclass, field
from typing import Optional

from overrides import override

from pyoniverse.items import CrawledInfoVO, ImageVO, ItemVO
from pyoniverse.items.schemas.event import BrandEventSchema
from pyoniverse.items.utils import get_timestamp


@dataclass(kw_only=True)
class BrandEventVO(ItemVO):
    """
    created_at, updated_at 은 자동으로 생성됩니다.
    필요한 경우, 직접 입력해도 됩니다.
    """

    crawled_info: CrawledInfoVO = field()
    created_at: int = field(default=None)
    updated_at: int = field(default=None)
    start_at: int = field()
    end_at: int = field()
    name: str = field()
    description: Optional[str] = field(default=None)
    image: ImageVO = field()

    def __post_init__(self):
        self.created_at = get_timestamp()
        self.updated_at = get_timestamp()

    @staticmethod
    @override
    def get_collection_name() -> str:
        return "events"

    @staticmethod
    def get_schema() -> BrandEventSchema:
        return BrandEventSchema()
