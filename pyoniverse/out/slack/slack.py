import json
import logging
import os
from dataclasses import asdict
from typing import Dict

import boto3
from boto3_type_annotations.sqs import Client

from pyoniverse.out.converter.type_to_message import TypeToMessageConverter
from pyoniverse.out.model.enum.message_enum import MessageTypeEnum
from pyoniverse.out.model.log_result import LogResult
from pyoniverse.out.model.message import Message


class SlackSender:
    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger("scrapy.sender")

    def send(self, message_type: MessageTypeEnum, data: Dict[str, LogResult]) -> bool:
        res: Message = self._convert(message_type, data)
        try:
            sqs_client: Client = boto3.client("sqs")
            sqs_queue_url: str = sqs_client.get_queue_url(
                QueueName=os.getenv("QUEUE_NAME")
            )["QueueUrl"]
            sqs_client.send_message(
                QueueUrl=sqs_queue_url,
                MessageBody=json.dumps(asdict(res)),
            )
        except Exception as e:
            self.logger.error(e)
            return False
        else:
            return True

    def _convert(
        self, message_type: MessageTypeEnum, data: Dict[str, LogResult]
    ) -> Message:
        message_converter = TypeToMessageConverter()
        msg = {
            "type": message_type.value,
            "source": "pyoniverse-crawler",
            "text": message_converter.convert(message_type=message_type, data=data),
            "ps": {k: str(asdict(v)) for k, v in data.items() if k != "summary"},
            "cc": ["윤영로"],
        }
        return Message.load(msg)
