from dataclasses import asdict

from pyoniverse.out.converter.converter import Converter
from pyoniverse.out.model.enum.message_enum import MessageTypeEnum


class TypeToMessageConverter(Converter):
    def convert(self, *args, **kwargs) -> str:
        """
        message_type: MessageTypeEnum
        data: Dict[str, LogResult]
        """
        format = "{message_type} Result: {result}"
        match kwargs["message_type"]:
            case MessageTypeEnum.SUCCESS:
                return format.format(
                    message_type=kwargs["message_type"],
                    result=asdict(kwargs["data"]["summary"]),
                )
            case MessageTypeEnum.ERROR:
                return format.format(
                    message_type=kwargs["message_type"],
                    result=asdict(kwargs["data"]["summary"]),
                )
            case MessageTypeEnum.DEBUG:
                return format.format(
                    message_type=kwargs["message_type"],
                    result=asdict(kwargs["data"]["summary"]),
                )
            case MessageTypeEnum.TEST:
                return format.format(
                    message_type=kwargs["message_type"],
                    result=asdict(kwargs["data"]["summary"]),
                )
            case _:
                raise NotImplementedError
