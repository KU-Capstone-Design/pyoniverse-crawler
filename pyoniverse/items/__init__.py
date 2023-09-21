from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, TypeVar

from marshmallow import Schema

from pyoniverse.items.schemas import (
    CrawledInfoSchema,
    EventSchema,
    ImageSchema,
    PriceSchema,
)


class ItemVO(metaclass=ABCMeta):
    @staticmethod
    @abstractmethod
    def get_schema() -> Schema:
        pass

    @staticmethod
    def get_collection_name() -> str:
        raise NotImplementedError


ItemType = TypeVar("ItemType", bound=ItemVO)


@dataclass(kw_only=True)
class CrawledInfoVO(ItemVO):
    spider: str = field()
    id: str = field()
    url: str = field()
    brand: int = field()

    @staticmethod
    def get_schema() -> Schema:
        return CrawledInfoSchema()


@dataclass(kw_only=True)
class PriceVO(ItemVO):
    value: float = field()
    currency: int = field()
    discounted_value: Optional[float] = field(default=None)

    @staticmethod
    def get_schema() -> Schema:
        return PriceSchema()


@dataclass(kw_only=True)
class ImageVO(ItemVO):
    """
    size 는 ImagePipeline 에서 채워집니다.
    """

    thumb: str = field(default=None)
    others: List[str] = field(default_factory=list)
    size: dict = field(
        default_factory=dict
    )  # {thumb: ImageSizeSchema, others: List[ImageSizeSchema]}

    @staticmethod
    def get_schema() -> Schema:
        return ImageSchema()


@dataclass(kw_only=True)
class EventVO(ItemVO):
    brand: int = field()
    id: int = field()

    @staticmethod
    def get_schema() -> Schema:
        return EventSchema()
