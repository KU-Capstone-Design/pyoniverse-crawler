import re
from datetime import datetime

from bs4 import BeautifulSoup
from scrapy import Request, Spider
from scrapy.http import HtmlResponse
from scrapy.shell import inspect_response

from pyoniverse.items import CrawledInfoVO, ImageVO
from pyoniverse.items.event import BrandEventVO
from pyoniverse.items.utils import convert_brand, get_timestamp


class CspaceWebSpider(Spider):
    name = "cspaceweb_event"
    brand = "cspace"

    allowed_domains = ["cspace.co.kr"]

    custom_settings = {
        "USER_AGENT_TYPE": "desktop",
        "download_delay": 5,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        "LOG_FILE": f"{name}.log",
    }

    base_url = "https://www.cspace.co.kr"

    list_path = "/board_event01/list.php?tn=board_event01"

    def start_requests(self):
        yield Request(url=self.base_url, callback=self.__start_request)

    def __start_request(self, response: HtmlResponse, **kwargs) -> Request:
        yield response.follow(self.list_path, callback=self.parse_list)

    def parse_list(self, response: HtmlResponse, **kwargs) -> Request:
        soup = BeautifulSoup(response.text, "html.parser")

        date_pattern = re.compile(r"\((\d{2}\.\d{2}\.\d{2})~(\d{2}\.\d{2}\.\d{2})\)")
        for event in soup.select(".list_gallery > ul > li"):
            detail_ref = event.select_one("a")["href"]
            thumb = self.base_url + event.select_one(".img img")["src"]
            title = event.select_one(".subject_text").text.strip()
            dates = date_pattern.search(title)
            start_at, end_at = dates.group(1), dates.group(2)
            start_at = datetime.strptime(start_at, "%y.%m.%d")
            end_at = datetime.strptime(end_at, "%y.%m.%d")
            title = date_pattern.sub("", title).strip()
            crawl_id = thumb.split("/")[-1].split(".")[0]
            yield response.follow(
                detail_ref,
                callback=self.parse,
                cb_kwargs={
                    "title": title,
                    "start_at": start_at,
                    "end_at": end_at,
                    "crawl_id": crawl_id,
                    "thumb": thumb,
                },
            )

            # pagination
            if len(soup.select("#page > option")) > 1:
                # pagination needs
                self.logger.error("Pagination Needs")

    def parse(self, response: HtmlResponse, **kwargs):
        soup = BeautifulSoup(response.text, "html.parser")
        frame = soup.select_one("#v_content_id")
        yield response.follow(frame["src"], self.__parse, cb_kwargs=kwargs)

    def __parse(self, response: HtmlResponse, **kwargs):
        soup = BeautifulSoup(response.text, "html.parser")
        imgs = [self.base_url + i["src"] for i in soup.select("#p_wrap img")]

        event = BrandEventVO(
            crawled_info=CrawledInfoVO(
                spider=self.name,
                brand=convert_brand(self.brand),
                id=kwargs["crawl_id"],
                url=response.url,
            ),
            name=kwargs["title"],
            image=ImageVO(thumb=kwargs["thumb"], others=imgs),
            start_at=get_timestamp(kwargs["start_at"]),
            end_at=get_timestamp(kwargs["end_at"]),
        )
        yield event
