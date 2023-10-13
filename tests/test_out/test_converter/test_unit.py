import os

import pytest

from pyoniverse.out.converter.type_to_message import TypeToMessageConverter
from pyoniverse.out.model.enum.message_enum import MessageTypeEnum
from pyoniverse.out.model.log_result import LogResult

if "tests" not in os.listdir():
    os.chdir("..")


@pytest.fixture
def data():
    return {
        "summary": LogResult(error_count=10, collected_count=5, elapsed_sec=3),
        "a": LogResult(error_count=3, collected_count=2, elapsed_sec=2),
        "b": LogResult(error_count=7, collected_count=3, elapsed_sec=3),
    }


def test_type_to_message_type_is_test(data):
    # given
    converter = TypeToMessageConverter()

    # when
    res = converter.convert(message_type=MessageTypeEnum.TEST, data=data)
    # then
    assert f"{MessageTypeEnum.TEST} Result: {data['summary']}"


def test_type_to_message_type_is_success(data):
    # given
    converter = TypeToMessageConverter()

    # when
    res = converter.convert(message_type=MessageTypeEnum.SUCCESS, data=data)
    # then
    assert f"{MessageTypeEnum.SUCCESS} Result: {data['summary']}"


def test_type_to_message_type_is_debug(data):
    # given
    converter = TypeToMessageConverter()

    # when
    res = converter.convert(message_type=MessageTypeEnum.DEBUG, data=data)
    # then
    assert f"{MessageTypeEnum.DEBUG} Result: {data['summary']}"


def test_type_to_message_type_is_error(data):
    # given
    converter = TypeToMessageConverter()
    # when
    res = converter.convert(message_type=MessageTypeEnum.TEST, data=data)
    # then
    assert f"{MessageTypeEnum.ERROR} Result: {data['summary']}"
