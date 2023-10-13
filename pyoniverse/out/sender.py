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

        self.__slack_sender = SlackSender(*args, **kwargs)

    def send_slack(
        self, message_type: MessageTypeEnum, data: Dict[str, LogResult]
    ) -> bool:
        return self.__slack_sender.send(message_type, data)
