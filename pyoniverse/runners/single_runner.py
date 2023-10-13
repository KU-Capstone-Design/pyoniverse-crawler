from overrides import override
from scrapy.crawler import CrawlerProcess

from pyoniverse.runners.runner import Runner


class SingleRunner(Runner):
    @classmethod
    @override
    def run(cls, *args, **kwargs):
        settings = cls._prepare(*args, **kwargs)
        runner: CrawlerProcess = CrawlerProcess(settings)
        runner.crawl(kwargs["spider"])
        runner.start()
