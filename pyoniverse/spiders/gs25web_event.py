import json
import re
from datetime import datetime

from bs4 import BeautifulSoup
from scrapy import FormRequest, Request, Spider
from scrapy.http import HtmlResponse

from pyoniverse.items import CrawledInfoVO, ImageVO
from pyoniverse.items.event import BrandEventVO
from pyoniverse.items.utils import convert_brand, get_timestamp


class Gs25WebEventSpider(Spider):
    name = "gs25web_event"
    brand = "GS25"

    custom_settings = {"USER_AGENT_TYPE": "mobile", "LOG_FILE": f"{name}.log"}

    allowed_domains = ["gs25.gsretail.com"]
    base_url = "http://gs25.gsretail.com"

    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "ko-KR,ko;q=0.9",
        "Connection": "keep-alive",
        # "Content-Length": content_length,
        # "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Host": "gs25.gsretail.com",
        "Origin": "http://gs25.gsretail.com",
        "X-Requested-With": "XMLHttpRequest",
    }

    def start_requests(self):
        yield Request(self.base_url, callback=self._start_request, headers=self.headers)

    def _start_request(self, response: HtmlResponse, **kwargs) -> Request:
        yield response.follow(
            "/gscvs/ko/customer-engagement/event/current-events",
            callback=self.parse_list,
            headers=self.headers,
        )

    def parse_list(self, response: HtmlResponse, **kwargs) -> Request:
        soup = BeautifulSoup(response.text, "html.parser")
        csrf = soup.select_one("input[name=CSRFToken]")["value"]

        yield FormRequest(
            self.base_url + f"/board/boardList?CSRFToken={csrf}",
            callback=self.__parse_list,
            formdata={
                "pageNum": "1",
                "pageSize": "30",
                "modelName": "event",
                "parameterList": "brandCode:GS25@!@eventFlag:CURRENT",
                "uiel": "Mobile",
            },
        )

    def __parse_list(self, response: HtmlResponse, **kwargs) -> Request:
        date_format = "%b %d, %Y %I:%M:%S %p"
        body = json.loads(response.text)
        for result in body["results"]:
            thumb = result["portraitThumbnail"].get("url") or result[
                "landscapeThumbnail"
            ].get("url")
            start_at = datetime.strptime(result["startDate"], date_format)
            end_at = datetime.strptime(result["endDate"], date_format)
            crawl_id = result["eventCode"]
            yield response.follow(
                f"/gscvs/ko/customer-engagement/event/detail/publishing?eventCode={crawl_id}",
                callback=self.parse,
                cb_kwargs={
                    "thumb": thumb,
                    "start_at": start_at,
                    "end_at": end_at,
                    "crawl_id": crawl_id,
                },
            )

        pagination = body["pagination"]
        if pagination["totalNumberOfResults"] > pagination["pageSize"]:
            self.logger.error("Pagination Required")

    def parse(self, response: HtmlResponse, **kwargs):
        soup = BeautifulSoup(response.text, "html.parser")
        info = soup.select_one("div.board_view.event_view")

        title = info.select_one(".bv_title").text.strip()
        date_format = re.compile(r"이벤트 기간\. \d{4}\.\d{2}\.\d{2} ~ \d{4}\.\d{2}\.\d{2}")
        title = date_format.sub("", title)
        title = re.sub(r"\s+", " ", title).strip()

        imgs = [i["src"] for i in info.select("img")]
        if desc := info.select_one(".invisible"):
            description = desc.text.strip()
        else:
            description = None

        event = BrandEventVO(
            crawled_info=CrawledInfoVO(
                spider=self.name,
                id=kwargs["crawl_id"],
                brand=convert_brand(self.brand),
                url=response.url,
            ),
            name=title,
            start_at=get_timestamp(kwargs["start_at"]),
            end_at=get_timestamp(kwargs["end_at"]),
            image=ImageVO(thumb=kwargs["thumb"], others=imgs),
            description=description,
        )
        yield event
