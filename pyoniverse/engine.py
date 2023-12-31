from pyoniverse.analyzer.analyzer import Analyzer
from pyoniverse.db.client import DBClient
from pyoniverse.out.model.enum.message_enum import MessageTypeEnum
from pyoniverse.out.sender import Sender
from pyoniverse.parser.log_parser.log_parser import LogParser
from pyoniverse.runners.all_runner import AllRunner
from pyoniverse.runners.single_runner import SingleRunner


class Engine:
    __instance = None

    @classmethod
    def __get_instance(cls, *args, **kwargs) -> "Engine":
        return cls.__instance

    @classmethod
    def instance(cls, *args, **kwargs) -> "Engine":
        cls.__instance = cls(*args, **kwargs)
        cls.instance = cls.__get_instance
        return cls.__instance

    def __init__(self, stage: str, spider: str, *args, **kwargs):
        self.__stage = stage
        self.__spider = spider
        self.__clear_db = kwargs.get("clear_db")

    def run(self, *args, **kwargs):
        if self.__stage in {"dev", "test"}:
            loglevel = "DEBUG"
        else:
            loglevel = "INFO"

        if self.__spider != "all":
            SingleRunner.run(
                spider=self.__spider, loglevel=loglevel, stage=self.__stage
            )
            return True
        else:
            if self.__clear_db:
                client = DBClient.instance()
                client.clear()
            AllRunner.run(loglevel=loglevel, stage=self.__stage)

            sender = Sender()
            sender.send(target="s3")

            log_parser = LogParser()
            analyzer = Analyzer()
            data = log_parser.parse()
            status = analyzer.analyze(data)
            if self.__stage in {"dev", "prod"}:
                sender.send(target="slack", message_type=status, data=data)
            return status == MessageTypeEnum.SUCCESS
