from dataclasses import asdict

from scrapy import Spider
from scrapy.exceptions import DropItem

from pyoniverse.items import ItemType, ItemVO
from pyoniverse.pipelines import BasePipeline


class ValidationPipeline(BasePipeline):
    """
    This pipeline is responsible for validating the data
    """

    def process_item(self, item: ItemType, spider: Spider) -> ItemType:
        """
        :param item:
        :param spider:
        :return: item
        Drop if the item is not valid
        """
        # Condition 1: Drop if the item is not fulfill the type requirements
        if not issubclass(type(item), ItemVO):
            raise DropItem(f"Item is not a valid ItemVO: {item}")
        # Condition 2: Drop if the item is not has collection
        if not hasattr(item, "get_collection_name"):
            raise DropItem(f"Item is not has collection name: {item}")
        # Condition 3: Drop if the item is missing or invalid fields
        schema = item.get_schema()
        reason: dict = schema.validate(asdict(item))
        if reason:
            raise DropItem(f"Item is not valid: {reason}")
        return item
