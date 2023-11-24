import logging
from typing import Dict

from pyoniverse.out.model.enum.message_enum import MessageTypeEnum
from pyoniverse.out.model.log_result import LogResult


class Analyzer:
    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger("scrapy.analyzer")

    def analyze(self, data: Dict[str, LogResult], *args, **kwargs) -> MessageTypeEnum:
        """
        stage: debug or test -> return same
        """
        if stage := kwargs.get("stage"):
            match stage:
                case "debug":
                    return MessageTypeEnum.DEBUG
                case "test":
                    return MessageTypeEnum.TEST
                case _:
                    raise NotImplementedError

        summarized = data["summary"]
        if (
            summarized.collected_count >= 5000
            and (100 * summarized.error_count / summarized.collected_count) <= 10
            and summarized.elapsed_sec <= 7200
        ):
            return MessageTypeEnum.SUCCESS
        else:
            return MessageTypeEnum.ERROR
