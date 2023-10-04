from typing import NoReturn

from scrapy.crawler import CrawlerRunner

from pyoniverse.runners.runner import Runner


class SingleRunner(Runner):
    @classmethod
    def _process(cls, runner: CrawlerRunner, *args, **kwargs) -> NoReturn:
        spider: str = kwargs["spider"]
        runner.crawl(spider)
