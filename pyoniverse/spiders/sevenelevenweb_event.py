import re
from datetime import datetime

from bs4 import BeautifulSoup
from scrapy import FormRequest, Request, Spider
from scrapy.http import HtmlResponse

from pyoniverse.items import CrawledInfoVO, ImageVO
from pyoniverse.items.event import BrandEventVO
from pyoniverse.items.utils import convert_brand, get_timestamp


class SevenElevenWebSpider(Spider):
    name = "sevenelevenweb_event"
    brand = "SEVEN ELEVEN"
    allowed_domains = ["7-eleven.co.kr"]
    base_url = "https://m.7-eleven.co.kr:444"

    custom_settings = {"USER_AGENT_TYPE": "mobile", "LOG_FILE": f"{name}.log"}

    main_path = "/product/eventList.asp"
    pagination_path = "/product/elistMoreAjax.asp"
    detail_path = "/product/eventView.asp"

    def start_requests(self):
        # Get cookies
        yield Request(url=self.base_url, callback=self.__start_request)

    def __start_request(self, response: HtmlResponse, **kwargs) -> Request:
        yield Request(url=self.base_url + self.main_path, callback=self.parse_list)

    def parse_list(self, response: HtmlResponse, **kwargs) -> Request:
        if "page_size" in kwargs:
            body = f"<html><body><ul id=listUl>{response.text}</ul></body></html>"
        else:
            body = response.text

        soup = BeautifulSoup(body, "html.parser")
        # pagination
        if not soup.select_one("p.complete"):
            page_size = kwargs.get("page_size", 15)
            yield FormRequest(
                self.base_url + self.pagination_path,
                callback=self.parse_list,
                formdata={"intPageSize": str(page_size)},
                cb_kwargs={"page_size": page_size + 5},
            )
        else:
            lst = soup.select("#listUl > li")
            for event in lst:
                status = event.select_one("p").text.strip()
                if status != "진행중":
                    return
                link = event.select_one("a")
                title = link.select_one("strong").text.strip()
                start_at, end_at = link.select_one("span").text.strip().split(" ~ ")
                start_at = datetime.strptime(start_at, "%Y-%m-%d")
                end_at = datetime.strptime(end_at, "%Y-%m-%d")
                crawl_id = re.search(r"fncGoView\((.+)\)", link["href"]).group(1)
                yield FormRequest(
                    self.base_url + self.detail_path,
                    callback=self.parse,
                    formdata={"seqNo": crawl_id},
                    cb_kwargs={
                        "title": title,
                        "start_at": start_at,
                        "end_at": end_at,
                        "crawl_id": crawl_id,
                    },
                )

    def parse(self, response: HtmlResponse, **kwargs):
        soup = BeautifulSoup(response.text, "html.parser")
        event = soup.select_one(".event_wrap_view > dl > dd")
        imgs = []
        for i in soup.select(".event_wrap_view > dl > dd > img"):
            i = i["src"]
            if i.startswith("/"):
                imgs.append(self.base_url + i)
            else:
                imgs.append(i)
        if imgs:
            thumb = imgs.pop(0)
        else:
            thumb = None
        description = event.text.strip()
        description = re.sub(r"(\s)+", r"\1", description).strip() or None

        event = BrandEventVO(
            crawled_info=CrawledInfoVO(
                spider=self.name,
                id=kwargs["crawl_id"],
                brand=convert_brand(self.brand),
                url=response.url,
            ),
            name=kwargs["title"],
            image=ImageVO(thumb=thumb, others=imgs),
            description=description,
            start_at=get_timestamp(kwargs["start_at"]),
            end_at=get_timestamp(kwargs["end_at"]),
        )
        yield event
