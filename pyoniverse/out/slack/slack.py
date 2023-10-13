from typing import Dict

from pyoniverse.out.converter.type_to_message import TypeToMessageConverter
from pyoniverse.out.model.enum.message_enum import MessageTypeEnum
from pyoniverse.out.model.log_result import LogResult
from pyoniverse.out.model.message import Message


class SlackSender:
    def __init__(self, *args, **kwargs):
        pass

    def send(self, message_type: MessageTypeEnum, data: Dict[str, LogResult]) -> bool:
        res: Message = self._convert(message_type, data)

    def _convert(
        self, message_type: MessageTypeEnum, data: Dict[str, LogResult]
    ) -> Message:
        message_converter = TypeToMessageConverter()
        msg = {
            "type": message_type,
            "source": "pyoniverse-crawler",
            "text": message_converter.convert(message_type=message_type, data=data),
            "ps": data,
            "cc": ["윤영로"],
        }
        return Message.load(msg)
