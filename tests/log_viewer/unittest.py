import datetime
import os
from pathlib import Path
from typing import Dict

from pyoniverse.log_viewer.log_viewer import LogViewer
from pyoniverse.log_viewer.model.log_result import LogResult


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


def test_log_viewer_parse():
    # given
    log_viewer = LogViewer()
    log_path = Path("./mock/mock.log")
    parsed_result = {
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
    # when
    res = log_viewer._parse(log_path)

    # then
    assert res == parsed_result


def test_log_viewer():
    # given
    log_viewer = LogViewer()
    log_files = set()
    for f in os.listdir():
        if f.endswith(".log"):
            log_files.add(f[:-4])
    # when
    res: Dict[str, LogResult] = log_viewer.result()

    # then
    assert set(res.keys()) == log_files
    for val in res.items():
        assert isinstance(val, LogResult)

    for key, val in res.items():
        assert val.collected_count >= 100
        assert val.error_count <= 10
        assert val.elapsed_sec <= 3600
    assert "summary" in res
    assert res["summary"].collected_count >= 5000
    assert res["summary"].total_error <= 50
