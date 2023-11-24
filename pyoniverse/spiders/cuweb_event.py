import json
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup
from scrapy import FormRequest, Request, Spider
from scrapy.http import Response

from pyoniverse.items import CrawledInfoVO, ImageVO
from pyoniverse.items.event import BrandEventVO
from pyoniverse.items.utils import convert_brand, get_timestamp


class CUWebEventSpider(Spider):
    name = "cuweb_event"
    brand = "CU"

    custom_settings = {"USER_AGENT_TYPE": "mobile", "LOG_FILE": f"{name}.log"}

    allowed_domains = ["www.pocketcu.co.kr", "cloud.pocketcu.co.kr"]
    base_url = "https://www.pocketcu.co.kr"
    img_base_url = "https://arqachylpmku8348141.cdn.ntruss.com"

    def start_requests(self) -> Request:
        # Cookie 가져오기
        yield Request(self.base_url, callback=self.__start_requests)

    def __start_requests(self, response: Response) -> Request:
        yield FormRequest(
            method="POST",
            url="https://cloud.pocketcu.co.kr:444/api/v1/event",
            callback=self.parse_list,
        )

    def parse_list(self, response: Response):
        body = json.loads(response.text)["eventList"]
        for event in body:
            start_date, end_date = (
                datetime.strptime(event["evtSYmd"], "%Y%m%d"),
                datetime.strptime(event["evtEYmd"], "%Y%m%d"),
            )
            if not event["bannerImg"].startswith("http"):
                if event["bannerImg"].startswith("/"):
                    banner = str(self.img_base_url + event["bannerImg"])
                else:
                    banner = str(self.img_base_url + "/" + event["bannerImg"])
            else:
                banner = event["bannerImg"]
            title = event["prdDispNm"]
            crawl_id = event["evtCd"]
            yield Request(
                self.base_url + f"/event/eventView/{crawl_id}",
                callback=self.parse,
                cb_kwargs={
                    "crawl_id": crawl_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "banner": banner,
                    "title": title,
                },
            )

    def parse(self, response: Response, **kwargs) -> BrandEventVO:
        soup = BeautifulSoup(response.text, "html.parser")
        event = soup.select_one(".event_area")
        imgs = []
        for i in event.select("img"):
            if i["src"].startswith("http"):
                imgs.append(i["src"])
                continue
            elif i["src"].startswith("//"):
                imgs.append("https:" + i["src"])
                continue
            elif i["src"].startswith("/"):
                imgs.append("https:/" + i["src"])
            elif i["src"].startswith(":"):
                imgs.append("https" + i["src"])
        # description = event.get_text().strip()
        # description = re.sub(r"(\s)+", r"\1", description)

        event = BrandEventVO(
            crawled_info=CrawledInfoVO(
                spider=self.name,
                brand=convert_brand(self.brand),
                id=kwargs["crawl_id"],
                url=response.url,
            ),
            start_at=get_timestamp(kwargs["start_date"]),
            end_at=get_timestamp(kwargs["end_date"]),
            name=kwargs["title"],
            description=None,
            image=ImageVO(thumb=kwargs["banner"], others=imgs),
        )
        yield event
