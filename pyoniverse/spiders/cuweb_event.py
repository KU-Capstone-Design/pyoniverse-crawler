import re
from datetime import datetime
from functools import reduce
from time import sleep

from bs4 import BeautifulSoup
from scrapy import FormRequest, Request, Spider
from scrapy.http import Response
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.python.failure import Failure

from pyoniverse.items import CrawledInfoVO, ImageVO
from pyoniverse.items.event import BrandEventVO
from pyoniverse.items.utils import convert_brand, get_timestamp


class CUWebEventSpider(Spider):
    name = "cuweb_event"
    brand = "CU"

    custom_settings = {
        "USER_AGENT_TYPE": "desktop",
    }
    base_url = "https://cu.bgfretail.com"
    event_url = "https://cu.bgfretail.com/brand_info/news_listAjax.do"
    event_detail_url = "https://cu.bgfretail.com/brand_info/news_view.do?category=brand_info&depth2=5&idx={idx}"

    allowed_domains = ["cu.bgfretail.com"]

    def start_requests(self) -> Request:
        # Cookie 가져오기
        yield Request(
            self.base_url, callback=self.__start_requests, errback=self.errback
        )

    def __start_requests(self, response: Response) -> Request:
        yield FormRequest(
            url=self.event_url,
            formdata={
                "idx": "0",
                "pageIndex": "1",
                "searchCondition": "",
                "search2": "",
                "searchKeyword": "",
            },
            callback=self.parse_list,
            errback=self.errback,
        )

    def parse_list(self, response: Response):
        soup = BeautifulSoup(response.text, "html.parser")

        rows = soup.select("tr")
        for row in rows:
            thumbnail = row.select_one(".preview_thum > img")
            if not thumbnail:
                self.logger.debug("Thumbnail not found")
                thumbnail = None
            else:
                thumbnail = thumbnail["src"]

            post_id = row.select_one(r"a[href^=javascript\:newsDetail]")["href"]
            post_id = re.search(r"newsDetail\('?\"?(\d+)'?\"?\)", post_id).group(1)

            body = response.request.body.decode()
            body = {k: v for k, v in [x.split("=") for x in body.split("&")]}
            body["idx"] = post_id
            yield FormRequest(
                url=self.event_detail_url.format(idx=post_id),
                formdata=body,
                callback=self.parse,
                errback=self.errback,
                meta={
                    "crawl_id": post_id,
                    "thumbnail": thumbnail,
                },
            )
        pagination = soup.select_one("#paging")
        cur_page = pagination.select_one("a.Current")
        next_page = cur_page.find_next_sibling("a")["onclick"]
        next_page = re.search(r"newsPage\(\'?\"?(\d+)\'?\"?\)", next_page).group(1)
        if int(next_page) != int(cur_page.text):
            yield FormRequest(
                url=self.event_url,
                formdata={
                    "idx": "0",
                    "pageIndex": next_page,
                    "searchCondition": "",
                    "search2": "",
                    "searchKeyword": "",
                },
                callback=self.parse_list,
                errback=self.errback,
            )

    def parse(self, response: Response, **kwargs) -> BrandEventVO:
        soup = BeautifulSoup(response.text, "html.parser")
        detail = soup.select_one("table[summary=상세]")
        head = detail.select_one("thead")
        body = detail.select_one("tbody")

        name = head.select_one("th").text.strip()
        written_at = head.select_one("th.date").text.strip()
        written_at = datetime.strptime(written_at, "%Y.%m.%d")
        # 현재 월만 가져오기
        if (
            written_at.year != datetime.now().year
            or written_at.month != datetime.now().month
        ):
            self.logger.debug(f"This event is not this month: {written_at} {response}")
            return None

        written_at = get_timestamp(written_at)
        infos = body.select("p")
        images = [info.select("img") for info in infos if info.select_one("img")]
        images = reduce(lambda x, y: x + y, images, [])
        images = [image["src"] for image in images]

        if not response.meta["thumbnail"] and len(images) > 0:
            self.logger.debug("Thumbnail not found, use first image as thumbnail")
            response.meta["thumbnail"] = images.pop(0)

        texts = "\n".join(
            [info.text.strip() for info in infos if not info.select_one("img")]
        )
        texts = re.sub(r"\r\n", r"\n", texts).strip()
        texts = re.sub(r"(\s)+", r"\1", texts).strip()

        res = BrandEventVO(
            crawled_info=CrawledInfoVO(
                spider=self.name,
                id=response.meta["crawl_id"],
                url=response.url,
                brand=convert_brand(self.brand),
            ),
            name=name,
            written_at=written_at,
            description=texts,
            image=ImageVO(thumb=response.meta["thumbnail"], others=images),
        )
        yield res

    def errback(self, failure: Failure):
        if failure.check(HttpError):
            req: Request = failure.value.response.request.copy()
            req.dont_filter = True
            self.logger.error("403 Forbidden: {}. Retry after 5 sec".format(req.url))
            sleep(5)
            yield req
        else:
            self.logger.error(repr(failure))
