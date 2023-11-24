import datetime
import os
from functools import reduce
from pathlib import Path
from typing import Dict

import pytest

from pyoniverse.out.model.log_result import LogResult
from pyoniverse.parser.log_parser.log_parser import LogParser


while "tests" not in os.listdir():
    os.chdir("..")


@pytest.fixture
def result_data():
    return {
        "downloader/request_bytes": 21030,
        "downloader/request_count": 44,
        "downloader/request_method_count/GET": 43,
        "downloader/request_method_count/POST": 1,
        "downloader/response_bytes": 22467168,
        "downloader/response_count": 44,
        "downloader/response_status_count/200": 43,
        "downloader/response_status_count/302": 1,
        "elapsed_time_seconds": 37.962657,
        "file_count": 31,
        "file_status_count/downloaded": 31,
        "finish_reason": "finished",
        "finish_time": datetime.datetime(2023, 10, 13, 2, 42, 25, 316402),
        "item_scraped_count": 8,
        "log_count/DEBUG": 1242,
        "log_count/ERROR": 1,
        "log_count/INFO": 11,
        "log_count/WARNING": 2,
        "memusage/max": 88870912,
        "memusage/startup": 88870912,
        "request_depth_max": 3,
        "response_received_count": 43,
        "scheduler/dequeued": 13,
        "scheduler/dequeued/memory": 13,
        "scheduler/enqueued": 13,
        "scheduler/enqueued/memory": 13,
        "spider_exceptions/AttributeError": 1,
        "start_time": datetime.datetime(2023, 10, 13, 2, 41, 47, 353745),
    }


@pytest.fixture
def log_results():
    return {
        "1": LogResult(collected_count=1, error_count=1, elapsed_sec=3),
        "2": LogResult(collected_count=3, error_count=2, elapsed_sec=1),
        "3": LogResult(collected_count=2, error_count=0, elapsed_sec=2),
        "4": LogResult(collected_count=5, error_count=3, elapsed_sec=5),
    }


def test_log_result():
    # given
    result_data = {
        "collected_count": 1,
        "error_count": 1,
        "elapsed_sec": 10,
        "some_bad_field": "bad",
    }
    # when
    log_result = LogResult.load(result_data)

    # then
    assert log_result.collected_count == result_data["collected_count"]
    assert log_result.error_count == result_data["error_count"]
    assert log_result.elapsed_sec == result_data["elapsed_sec"]


def test_log_parser_parse(result_data):
    # given
    log_parser = LogParser()
    log_path = Path("tests/mock/mock.log")
    # when
    res = log_parser._parse(log_path)

    # then
    assert res == result_data


def test_log_parser_convert(result_data):
    # given
    log_parser = LogParser()
    error_count = result_data["log_count/ERROR"]
    collected_count = result_data["item_scraped_count"]
    elapsed_sec = int(result_data["elapsed_time_seconds"])

    # when
    res = log_parser._convert(result_data)

    # then
    assert res.collected_count == collected_count
    assert res.error_count == error_count
    assert res.elapsed_sec == elapsed_sec


def test_log_parser_summary(log_results):
    # given
    log_parser = LogParser()
    collected_count = reduce(
        lambda acc, cur: acc + cur.collected_count, log_results.values(), 0
    )
    error_count = reduce(
        lambda acc, cur: acc + cur.error_count, log_results.values(), 0
    )
    elapsed_sec = max(log_results.values(), key=lambda x: x.elapsed_sec).elapsed_sec

    # when
    res = log_parser._summary(log_results)

    # then
    assert res.collected_count == collected_count
    assert res.error_count == error_count
    assert res.elapsed_sec == elapsed_sec


def test_log_parser():
    # given
    log_parser = LogParser()
    root_dir = Path("tests/mock")
    log_files = set()
    for f in os.listdir(root_dir):
        if f.endswith(".log"):
            log_files.add(f[:-4])
    # when
    res: Dict[str, LogResult] = log_parser.parse(root_dir)

    # then
    assert set(res.keys()) == log_files.union({"summary"})
    for val in res.values():
        assert isinstance(val, LogResult)
