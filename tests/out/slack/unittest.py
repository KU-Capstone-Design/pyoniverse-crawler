from typing import Dict

import pytest

from pyoniverse.out.model.enum.message_enum import MessageTypeEnum
from pyoniverse.out.model.log_result import LogResult
from pyoniverse.out.model.message import Message
from pyoniverse.out.sender import Sender
from pyoniverse.out.slack.slack import SlackSender


@pytest.fixture
def data() -> Dict[str, LogResult]:
    return {
        "test1": LogResult(collected_count=1, error_count=0, elapsed_sec=10),
        "test2": LogResult(collected_count=2, error_count=1, elapsed_sec=2),
        "summary": LogResult(collected_count=3, error_count=1, elapsed_sec=10),
    }


def test_convert_to_msg(data):
    # given
    slack_sender = SlackSender()
    msg = Message(
        type=MessageTypeEnum.TEST,
        source="pyoniverse-crawler",
        text="test_message",
        ps=data,
        cc=["윤영로"],
    )
    # when
    res = slack_sender._convert(MessageTypeEnum.TEST, data)
    # then
    assert msg == res


def test_send_slack(data: Dict[str, LogResult]):
    # given
    sender = Sender()
    # when
    res = sender.send_slack(MessageTypeEnum.TEST, data)
    # then
    assert res is True
