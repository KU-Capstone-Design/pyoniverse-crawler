from typing import Dict

from pyoniverse.runners.all_runner import AllRunner


def test_acceptance_spec():
    # given
    runner = AllRunner.run(loglevel="DEBUG", stage="test")
    log_viewer = LogViewer()
    # when
    res: Dict[str, LogResult] = log_viewer.result()

    # then
    assert "summary" in res
    assert res["summary"].collected_count >= 5000
    assert res["summary"].error_count <= 50
    assert res["summary"].elapsed_sec <= 3600
