import logging
import os
from time import sleep

from pymongo import MongoClient, WriteConcern
from pymongo.errors import ConfigurationError


class DBClient:
    """
    최초 실행된 인스턴스로 고정
    """

    __instance = None

    @classmethod
    def __get_instance(cls, *args, **kwargs) -> "DBClient":
        """
        URI: connection uri
        DB: db name
        """
        return cls.__instance

    @classmethod
    def instance(cls, *args, **kwargs) -> "DBClient":
        """
        URI: connection uri
        DB: db name
        """
        cls.__instance = cls(*args, **kwargs)
        # 이후 instance 실행에서 변경 불가능하게
        cls.instance = cls.__get_instance
        return cls.__instance

    def __init__(self, *args, **kwargs):
        """
        URI: connection uri
        DB: db name
        """
        self.__client = MongoClient(kwargs.get("URI", os.getenv("MONGO_URI")))
        self.__db = kwargs.get("DB", os.getenv("MONGO_DB"))

        try:
            self.__client.admin.command("ping")
        except ConfigurationError:
            logging.error("Cannot connect to client")
            exit(1)

    def clear(self):
        """
        DB의 모든 컬렉션 데이터 제거
        """
        write_db = self.__client.get_database(
            self.__db, write_concern=WriteConcern(w="majority", wtimeout=60)
        )
        for col in write_db.list_collection_names():
            write_db.get_collection(col).delete_many({})
            sleep(10)
        return
