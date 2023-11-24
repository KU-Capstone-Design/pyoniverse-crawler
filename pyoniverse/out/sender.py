import logging

from pyoniverse.out.s3.s3 import S3Sender
from pyoniverse.out.slack.slack import SlackSender


class Sender:
    """
    Facade Pattern
    """

    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger("scrapy.sender")
        self.logger.setLevel(logging.INFO)

    def send(
        self,
        target: str,
        **kwargs,
    ) -> bool:
        match target:
            case "slack":
                res = SlackSender().send(
                    message_type=kwargs["message_type"], data=kwargs["data"]
                )
            case "s3":
                res = S3Sender().send()
            case _:
                raise NotImplementedError

        if res:
            self.logger.info(f"send to {target} success.")
        else:
            self.logger.error(f"send to {target} failed")
        return res
