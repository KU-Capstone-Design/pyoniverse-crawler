from dataclasses import asdict

from pymongo import MongoClient, WriteConcern
from pymongo.database import Database
from pymongo.read_preferences import SecondaryPreferred
from pymongo.results import UpdateResult
from scrapy import Spider

from pyoniverse.items.product import ProductVO


class DatabasePipeline:
    """
    MongoDB에 아이템을 저장한다
    """

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get("MONGODB_URI"),
            mongo_db=crawler.settings.get("MONGODB_DATABASE"),
            stage=crawler.settings.get("STAGE"),
        )

    def __init__(self, mongo_uri, mongo_db, stage):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.stage = stage
        self.__client: MongoClient = None
        self.read_db: Database = None
        self.write_db: Database = None

    def open_spider(self, spider: Spider):
        self.__client = MongoClient(self.mongo_uri)
        self.read_db = self.__client.get_database(
            self.mongo_db, read_preference=SecondaryPreferred()
        )
        self.write_db = self.__client.get_database(
            self.mongo_db, write_concern=WriteConcern(w="majority")
        )

    def close_spider(self, spider):
        self.__client.close()

    def process_item(self, item: ProductVO, spider: Spider) -> ProductVO:
        """
        :param item: Item to be processed
        :param spider: Current Spider
        :return: Processed Item
        """
        if spider.settings.get("STAGE") == "test":
            # Development mode - Don't save item to database
            return item
        else:
            query = {"crawled_info": asdict(item.crawled_info)}
            update = {"$set": asdict(item)}
            res: UpdateResult = self.write_db.get_collection("products").update_one(
                query,
                update,
                upsert=True,
                hint=[("crawled_info.spider", 1), ("crawled_info.id", 1)],
            )
            if res.matched_count == 0:
                spider.logger.info(f"New item saved: {asdict(item.crawled_info)}")
            elif res.modified_count == 0:
                spider.logger.info(f"Item already exists: {asdict(item.crawled_info)}")
            else:
                spider.logger.info(f"Item updated: {asdict(item.crawled_info)}")
            return item
