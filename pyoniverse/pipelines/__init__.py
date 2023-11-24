from abc import ABCMeta, abstractmethod

from scrapy import Spider

from pyoniverse.items import ItemType


class BasePipeline(metaclass=ABCMeta):
    @abstractmethod
    def process_item(self, item: ItemType, spider: Spider) -> ItemType:
        """
        :param item: Item to be processed
        :param spider: Current Spider
        :return: Processed Item
        """
        pass
