import logging
import os
from abc import ABCMeta, abstractmethod

from scrapy.settings import Settings
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings


class Runner(metaclass=ABCMeta):
    logger = logging.getLogger("scrapy.runner")

    @classmethod
    @abstractmethod
    def run(cls, *args, **kwargs):
        pass

    @classmethod
    def _prepare(cls, *args, **kwargs) -> Settings:
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
