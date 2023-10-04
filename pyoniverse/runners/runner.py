import logging
import os
from abc import ABCMeta, abstractmethod
from typing import NoReturn

from scrapy.crawler import CrawlerRunner
from scrapy.settings import Settings
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
from twisted.internet import reactor


class Runner(metaclass=ABCMeta):
    logger = logging.getLogger("scrapy.runner")

    @classmethod
    def run(cls, *args, **kwargs):
        settings = cls.__prepare(*args, **kwargs)
        runner = CrawlerRunner(settings)
        cls._process(runner, *args, **kwargs)
        d = runner.join()
        d.addBoth(lambda _: reactor.stop())
        reactor.run()
        cls.logger.info("The runner ends")
        return

    @classmethod
    def __prepare(cls, *args, **kwargs) -> Settings:
        settings = get_project_settings()
        settings["LOG_LEVEL"] = kwargs.get("loglevel", "DEBUG")
        settings["LOG_FILE"] = "debug.json"  # default log file
        settings["STAGE"] = kwargs["stage"]
        settings["MONGO_URI"] = os.getenv("MONGO_URI")
        settings["MONGO_DB"] = os.getenv("MONGO_DB")
        configure_logging(settings)
        cls.logger.info(
            f"Stage: {settings['STAGE']}, Log Level: {settings['LOG_LEVEL']}"
        )
        return settings

    @classmethod
    @abstractmethod
    def _process(cls, runner: CrawlerRunner, *args, **kwargs) -> NoReturn:
        pass
