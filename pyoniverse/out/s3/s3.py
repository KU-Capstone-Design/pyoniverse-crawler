import logging
import os

import boto3
from boto3_type_annotations.s3 import Client


class S3Sender:
    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger("scrapy.sender")

    def send(self, *args, **kwargs) -> bool:
        """
        log files 를 `pyoniverse-log` 로 이동
        """
        s3: Client = boto3.client("s3")
        for f in os.listdir():
            if not f.endswith(".log"):
                continue
            try:
                s3.upload_file(
                    f, Bucket=os.getenv("S3_BUCKET"), Key=f"{os.getenv('S3_KEY')}/{f}"
                )
            except Exception as e:
                self.logger.error(e)
                return False
        return True
