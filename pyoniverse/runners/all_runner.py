from pathlib import Path
from typing import NoReturn

from overrides import override
from scrapy.crawler import CrawlerRunner

from pyoniverse.runners.runner import Runner


class AllRunner(Runner):
    @classmethod
    @override
    def _process(cls, runner: CrawlerRunner, *args, **kwargs) -> NoReturn:
        spider_dir = Path("pyoniverse/spiders")
        for spider in spider_dir.glob("*.py"):
            if not spider.name.startswith("__"):
                name = spider.with_suffix("").stem
                runner.crawl(name)
                cls.logger.info(f"Run {name}")
