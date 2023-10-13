import os
from typing import Dict, List

import pytest

from pyoniverse.analyzer.analyzer import Analyzer
from pyoniverse.out.model.enum.message_enum import MessageTypeEnum
from pyoniverse.out.model.log_result import LogResult


if "tests" not in os.listdir():
    os.chdir("..")


@pytest.fixture
def success_data() -> Dict[str, LogResult]:
    return {
        "summary": LogResult(collected_count=5000, error_count=50, elapsed_sec=7200)
    }


@pytest.fixture
def failed_data() -> List[Dict[str, LogResult]]:
    return [
        {"summary": LogResult(collected_count=4999, error_count=50, elapsed_sec=7200)},
        {"summary": LogResult(collected_count=5000, error_count=501, elapsed_sec=7200)},
        {"summary": LogResult(collected_count=5000, error_count=50, elapsed_sec=7201)},
    ]


def test_analyzer(
    success_data: Dict[str, LogResult], failed_data: List[Dict[str, LogResult]]
):
    # given
    analyzer = Analyzer()

    # when
    success_status = analyzer.analyze(success_data)
    # then
    assert success_status == MessageTypeEnum.SUCCESS

    # when
    failed_statuses = [analyzer.analyze(d) for d in failed_data]
    assert all(map(lambda x: x == MessageTypeEnum.ERROR, failed_statuses))

    # when
    debug_status = analyzer.analyze(success_data, stage="debug")
    # then
    assert debug_status == MessageTypeEnum.DEBUG

    # when
    debug_status = analyzer.analyze(success_data, stage="test")
    # then
    assert debug_status == MessageTypeEnum.TEST
