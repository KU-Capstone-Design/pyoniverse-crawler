import logging
from typing import Dict

from pyoniverse.out.model.enum.message_enum import MessageTypeEnum
from pyoniverse.out.model.log_result import LogResult
from pyoniverse.out.slack.slack import SlackSender


class Sender:
    """
    Facade Pattern
    """

    def __init__(self, target, *args, **kwargs):
        self.logger = logging.getLogger("scrapy.sender")
        self.logger.setLevel(logging.INFO)
        self.__target = target

    def send(self, message_type: MessageTypeEnum, data: Dict[str, LogResult]) -> bool:
        match self.__target:
            case "slack":
                return SlackSender().send(message_type=message_type, data=data)
            case _:
                raise NotImplementedError
