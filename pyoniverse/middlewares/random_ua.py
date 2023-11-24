import json
from random import choice

from scrapy import Request
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware


class RandomUserAgentMiddleware(UserAgentMiddleware):
    """This middleware allows spiders to override the user_agent"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ua_type = "desktop"
        self.user_agents = []

    @classmethod
    def from_crawler(cls, crawler):
        o = super().from_crawler(crawler)
        o.ua_type = crawler.settings.get("USER_AGENT_TYPE", "desktop")
        with open(f"pyoniverse/middlewares/{o.ua_type}_ua.json", "r") as f:
            o.user_agents = [ua["ua"] for ua in json.load(f)]
        return o

    def process_request(self, request: Request, spider):
        if self.user_agents:
            request.headers.setdefault(b"User-Agent", choice(self.user_agents))
