from abc import ABCMeta, abstractmethod
from dataclasses import KW_ONLY, dataclass, field
from typing import List, TypeVar

from marshmallow import Schema

from pyoniverse.items.schemas import CrawledInfoSchema, ImageSchema, PriceSchema


class ItemVO(metaclass=ABCMeta):
    @staticmethod
    @abstractmethod
    def get_schema() -> Schema:
        pass


ItemType = TypeVar("ItemType", bound=ItemVO)


@dataclass
class CrawledInfoVO(ItemVO):
    _: KW_ONLY
    spider: str = field()
    id: str = field()
    url: str = field()

    @staticmethod
    def get_schema() -> Schema:
        return CrawledInfoSchema()


@dataclass
class PriceVO(ItemVO):
    _: KW_ONLY
    value: float = field()
    currency: int = field()

    @staticmethod
    def get_schema() -> Schema:
        return PriceSchema()


@dataclass
class ImageVO(ItemVO):
    _: KW_ONLY
    thumb: str = field()
    others: List[str] = field(default_factory=list)

    @staticmethod
    def get_schema() -> Schema:
        return ImageSchema()
