from scrapy import Request, Spider
from scrapy.shell import inspect_response


class Emart24WebSpider(Spider):
    name = "emart24web"
    allowed_domains = ["emart24.co.kr"]
    base_url = "http://www.emart24.co.kr"
    custom_settings = {"USER_AGENT_TYPE": "mobile"}

    def start_requests(self):
        yield Request(url=self.base_url, callback=self.parse_list)

    def parse_list(self, response):
        inspect_response(response, self)
