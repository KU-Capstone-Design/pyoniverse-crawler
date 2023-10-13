import os
from typing import Dict

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
