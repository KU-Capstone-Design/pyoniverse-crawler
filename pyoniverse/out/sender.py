import logging
from typing import Dict

from pyoniverse.out.model.enum.message_enum import MessageTypeEnum
from pyoniverse.out.model.log_result import LogResult
from pyoniverse.out.slack.slack import SlackSender


class Sender:
    """
    Facade Pattern
    """

    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger("scrapy.sender")
        self.logger.setLevel(logging.INFO)

    def send(
        self, target: str, message_type: MessageTypeEnum, data: Dict[str, LogResult]
    ) -> bool:
        match target:
            case "slack":
                res = SlackSender().send(message_type=message_type, data=data)
            case _:
                raise NotImplementedError

        if res:
            self.logger.info(f"send to {target} success.")
        else:
            self.logger.error(f"send to {target} failed")
        return res
