from dataclasses import KW_ONLY, dataclass, field
from typing import List


@dataclass
class CrawledInfoVO:
    _: KW_ONLY
    spider: str = field()
    id: str = field()
    url: str = field()


@dataclass
class PriceVO:
    _: KW_ONLY
    value: float = field()
    currency: int = field()


@dataclass
class ImageVO:
    _: KW_ONLY
    thumb: str = field()
    others: List[str] = field()
