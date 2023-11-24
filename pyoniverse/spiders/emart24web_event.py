import re
from datetime import datetime

from bs4 import BeautifulSoup
from scrapy import Request, Spider
from scrapy.http import HtmlResponse

from pyoniverse.items import CrawledInfoVO, ImageVO
from pyoniverse.items.event import BrandEventVO
from pyoniverse.items.utils import convert_brand, get_timestamp


class Emart24WebSpider(Spider):
    """
    Mobile web spider for emart24.co.kr
    """

    name = "emart24web_event"
    brand = "emart24"
    allowed_domains = ["emart24.co.kr"]
    custom_settings = {
        "USER_AGENT_TYPE": "mobile",
        "LOG_FILE": f"{name}.log",
    }

    base_url = "https://m.emart24.co.kr"
    list_path = "/event/ing"

    def start_requests(self):
        yield Request(self.base_url, callback=self.__start_request)

    def __start_request(self, response: HtmlResponse, **kwargs) -> Request:
        yield response.follow(self.list_path, callback=self.parse_list)

    def parse_list(self, response: HtmlResponse, **kwargs) -> Request:
        soup = BeautifulSoup(response.text, "html.parser")

        for event in soup.select("#eTab1 > a"):
            ref = event["href"]
            thumb = event.select_one(".eventImg > img")["src"]
            dates = event.select_one("p > span").text
            dates = re.sub(r"\s+", " ", dates).strip()
            start_at, end_at = dates.split(" ~ ")
            start_at = datetime.strptime(start_at, "%Y.%m.%d")
            end_at = datetime.strptime(end_at, "%Y.%m.%d")
            title = event.select_one("p").text.strip().split("\n")[-1].strip()
            crawl_id = ref.split("/")[-1]

            yield response.follow(
                ref,
                callback=self.parse,
                cb_kwargs={
                    "title": title,
                    "thumb": thumb,
                    "start_at": start_at,
                    "end_at": end_at,
                    "crawl_id": crawl_id,
                },
            )

    def parse(self, response: HtmlResponse, **kwargs):
        soup = BeautifulSoup(response.text, "html.parser")
        imgs = [i["src"] for i in soup.select(".contentWrap > img")]

        event = BrandEventVO(
            crawled_info=CrawledInfoVO(
                spider=self.name,
                id=kwargs["crawl_id"],
                brand=convert_brand(self.brand),
                url=response.url,
            ),
            name=kwargs["title"],
            image=ImageVO(thumb=kwargs["thumb"], others=imgs),
            start_at=get_timestamp(kwargs["start_at"]),
            end_at=get_timestamp(kwargs["end_at"]),
        )
        yield event
