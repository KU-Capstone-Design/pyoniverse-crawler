import os
import re
from pathlib import Path
from typing import Dict, Optional
import datetime

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
            log_result = self._parse(Path(root_dir) / f)
            res[log_name] = log_result
        return res

    def _parse(self, log_path: Path) -> Optional[LogResult]:
        with open(log_path, "r") as fd:
            context = fd.read()
            stats = re.search(r"Dumping Scrapy stats:\n(\{.+\})", context, re.DOTALL)
            if not stats:
                return None
            else:
                res = eval(stats.group(1))
                return res
