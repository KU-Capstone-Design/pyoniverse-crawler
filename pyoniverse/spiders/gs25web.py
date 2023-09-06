import json
from pathlib import Path
from time import sleep

from bs4 import BeautifulSoup
from scrapy import Request, Spider
from scrapy.exceptions import DropItem
from scrapy.http import HtmlResponse
from scrapy.http.request.form import FormRequest
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.python.failure import Failure

from pyoniverse.items import CrawledInfoVO, EventVO, ImageVO, ItemType, PriceVO
from pyoniverse.items.product import ProductVO
from pyoniverse.items.utils import convert_brand, convert_currency, convert_event


class Gs25WebSpider(Spider):
    name = "gs25web"
    brand = "GS25"

    allowed_domains = ["gs25.gsretail.com"]
    base_url = "http://gs25.gsretail.com"

    start_urls = {
        "event": "http://gs25.gsretail.com/gscvs/ko/products/event-goods",
        "youus": "http://gs25.gsretail.com/gscvs/ko/products/youus-main",
    }

    search_urls = {
        "event": "http://gs25.gsretail.com/gscvs/ko/products/event-goods-search",
    }

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

    custom_settings = {
        "DOWNLOAD_DELAY": 5,
    }

    def start_requests(self):
        for key, url in self.start_urls.items():
            if key == "event":
                # Page 는 1부터 시작합니다.
                # yield Request(
                #     url,
                #     callback=self.parse_event_home,
                #     headers=self.headers,
                #     cb_kwargs={"type": "event", "page": 1},
                # )
                pass
            elif key == "youus":
                yield Request(
                    url,
                    callback=self.parse_youus,
                    headers=self.headers,
                    cb_kwargs={"type": "youus", "page": 1},
                )
            else:
                raise RuntimeError("Unknown key: {}".format(key))

    def parse_event_home(self, response: HtmlResponse, **kwargs) -> ItemType:
        soup = BeautifulSoup(response.body, "html.parser")
        form = soup.select_one("#CSRFForm")
        if not form:
            raise RuntimeError("Can't find event post action")

        csrf_token = form.select_one("input")["value"]
        req_url = self.search_urls["event"]
        query = "CSRFToken={}".format(csrf_token)

        form_data = {
            "pageNum": str(kwargs["page"]),
            "pageSize": "8",
            "searchType": "",
            "searchWord": "",
            "parameterList": "TOTAL",
        }
        self.logger.debug(f"Form data: {form_data}")

        header = self.headers.copy()
        yield FormRequest(
            url=f"{req_url}?{query}",
            callback=self.parse_event,
            errback=self.errback,
            formdata=form_data,
            cb_kwargs=kwargs,
            headers=header,
            dont_filter=True,
        )

    def parse_youus(self, response: HtmlResponse, **kwargs) -> ItemType:
        """
        :param response:
        :param kwargs:
        :return:
        GS25 의 특화 상품 리스트
        """

    def parse_event(self, response: HtmlResponse, **kwargs) -> ItemType:
        body = response.json()
        if isinstance(body, str):
            body = json.loads(body)
        pagination = body["pagination"]
        results = body["results"]

        if not results:
            return

        for result in results:
            result = {k: v for k, v in result.items() if not k.endswith("Old")}
            product_name = result["goodsNm"]
            event_type = result.get("eventTypeNm")
            if event_type and event_type == "덤증정":
                event_type = "GIFT"

            product_price = float(result["price"])
            product_img = result.get("attFileNm")
            if not product_img:
                raise DropItem("No image: {}".format(product_name))
            # product_id = image_path 의 마지막 부분을 id 로 사용합니다.
            product_id = Path(product_img).stem

            product: ProductVO = ProductVO(
                crawled_info=CrawledInfoVO(
                    spider=self.name, url=response.url, id=product_id
                ),
                name=product_name,
                price=PriceVO(value=product_price, currency=convert_currency("KRW")),
                image=ImageVO(thumb=product_img),
                events=[
                    EventVO(
                        id=convert_event(event_type), brand=convert_brand(self.brand)
                    )
                ]
                if event_type
                else [],
            )
            yield product

        current_page = int(kwargs["page"])
        self.logger.info(f"Next page: {current_page + 1}/{pagination['numberOfPages']}")
        yield Request(
            self.start_urls["event"],
            callback=self.parse_event_home,
            headers=self.headers,
            cb_kwargs={"type": "event", "page": current_page + 1},
            dont_filter=True,
        )

    def errback(self, failure: Failure):
        # Retry if 403 Forbidden
        if failure.check(HttpError) and failure.value.response.status == 403:
            req: Request = failure.value.response.request.copy()
            req.dont_filter = True
            self.logger.error("403 Forbidden: {}. Retry after 5 sec".format(req.url))
            sleep(5)
            match req.cb_kwargs["type"]:
                # Reset cookies
                case "event":
                    yield Request(
                        self.start_urls["event"],
                        callback=self.parse_event_home,
                        headers=self.headers,
                        cb_kwargs=req.cb_kwargs,
                        dont_filter=True,
                    )
                case "youus":
                    yield Request(
                        self.start_urls["youus"],
                        callback=self.parse_youus,
                        headers=self.headers,
                        cb_kwargs=req.cb_kwargs,
                        dont_filter=True,
                    )
                case _:
                    raise RuntimeError("Unknown type: {}".format(req.cb_kwargs["type"]))
        else:
            self.logger.error(repr(failure))
