from enum import Enum, unique


@unique
class MessageTypeEnum(str, Enum):
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    TEST = "TEST"
    DEBUG = "DEBUG"
