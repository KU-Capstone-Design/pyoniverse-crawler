import os
import re
from pathlib import Path
from typing import Dict, Optional

from pyoniverse.log_viewer.model.log_result import LogResult


class LogViewer:
    def __init__(self, *args, **kwargs):
        pass

    def result(self, root_dir=".") -> Dict[str, LogResult]:
        res = {}
        for f in os.listdir(root_dir):
            if not f.endswith(".log"):
                continue
            log_name = f[:-4]  # .log 제외
            if log_result := self._parse(Path(root_dir) / f):
                res[log_name] = self._convert(log_result)

        res["summary"] = self._summary(res)
        return res

    def _parse(self, log_path: Path) -> Optional[dict]:
        with open(log_path, "r") as fd:
            context = fd.read()
            stats = re.search(r"Dumping Scrapy stats:\n(\{.+\})", context, re.DOTALL)
            if not stats:
                return None
            else:
                res = eval(stats.group(1))
                return res

    def _convert(self, data: dict) -> LogResult:
        res = LogResult(
            collected_count=data["item_scraped_count"],
            error_count=data["log_count/ERROR"],
            elapsed_sec=int(data["elapsed_time_seconds"]),
        )
        return res

    def _summary(self, res: Dict[str, LogResult]) -> LogResult:
        collected_count = 0
        error_count = 0
        elapsed_sec = 0
        for v in res.values():
            collected_count += v.collected_count
            error_count += v.error_count
            elapsed_sec = max(elapsed_sec, v.elapsed_sec)
        return LogResult(
            collected_count=collected_count,
            error_count=error_count,
            elapsed_sec=elapsed_sec,
        )
