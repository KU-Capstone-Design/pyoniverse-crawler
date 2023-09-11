from dataclasses import asdict, fields

from overrides import override
from pymongo import MongoClient, WriteConcern
from pymongo.database import Database
from pymongo.read_preferences import SecondaryPreferred
from pymongo.results import UpdateResult
from scrapy import Spider

from pyoniverse.items import EventVO, ItemType
from pyoniverse.pipelines import BasePipeline


class MongoDBPipeline(BasePipeline):
    """
    MongoDB에 아이템을 저장한다
    """

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get("MONGO_URI"),
            mongo_db=crawler.settings.get("MONGO_DB"),
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

    @override
    def process_item(self, item: ItemType, spider: Spider) -> ItemType:
        """
        :param item: Item to be processed
        :param spider: Current Spider
        :return: Processed Item
        """
        if self.stage == "test":
            # Development mode - Don't save item to database
            return item
        else:
            coll: str = item.get_collection_name()
            query = {
                "crawled_info.spider": item.crawled_info.spider,
                "crawled_info.id": item.crawled_info.id,
            }
            hint = [("crawled_info.spider", 1), ("crawled_info.id", 1)]
            prv_item = self.read_db.get_collection(coll).find_one(
                query, {"_id": False}, hint=hint
            )

            if prv_item:
                if coll == "products":
                    # item 에서 null 인 값은 이전 값으로 대체 && events 는 합친다.
                    for _field in fields(item):
                        if _field.name == "events":
                            continue
                        if prv_val := prv_item.get(_field.name):
                            if getattr(item, _field.name) is None:
                                setattr(item, _field.name, prv_val)
                    cur_events = list(map(asdict, item.events))
                    prv_events = prv_item.get("events", [])
                    events = cur_events + prv_events
                    events = set(map(lambda x: (x["brand"], x["id"]), events))
                    events = list(map(lambda x: {"brand": x[0], "id": x[1]}, events))
                    item.events = [EventVO(**event) for event in events]

                # created_at 은 이전 값으로 대체
                item.created_at = prv_item["created_at"]

            update = {"$set": asdict(item)}
            res: UpdateResult = self.write_db.get_collection("products").update_one(
                query,
                update,
                upsert=True,
                hint=hint,
            )
            if res.matched_count == 0:
                spider.logger.info(f"New item saved: {asdict(item.crawled_info)}")
            elif res.modified_count == 0:
                spider.logger.info(f"Item already exists: {asdict(item.crawled_info)}")
            else:
                spider.logger.info(f"Item updated: {asdict(item.crawled_info)}")
            return item
