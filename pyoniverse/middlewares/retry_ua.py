import json
from random import choice

from scrapy import Request
from scrapy.downloadermiddlewares.retry import RetryMiddleware


class RetryRandomUserAgentMiddleware(RetryMiddleware):
    def __init__(self, ua_type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ua_type = ua_type
        with open(f"pyoniverse/middlewares/{ua_type}_ua.json", "r") as f:
            self.user_agents = [ua["ua"] for ua in json.load(f)]

    @classmethod
    def from_crawler(cls, crawler):
        ua_type = crawler.settings.get("USER_AGENT_TYPE", "desktop")
        return cls(ua_type, crawler.settings)

    def process_response(self, request: Request, response, spider):
        request.headers.setdefault(b"User-Agent", choice(self.user_agents))
        return super().process_response(request, response, spider)

    def process_exception(self, request, exception, spider):
        request.headers.setdefault(b"User-Agent", choice(self.user_agents))
        return super().process_exception(request, exception, spider)
