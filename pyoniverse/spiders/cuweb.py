import re
from time import sleep

from bs4 import BeautifulSoup
from scrapy import FormRequest, Request, Spider
from scrapy.exceptions import DropItem
from scrapy.http import HtmlResponse
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.python.failure import Failure

from pyoniverse.items import CrawledInfoVO, EventVO, ImageVO, ItemType, PriceVO
from pyoniverse.items.product import ProductVO
from pyoniverse.items.utils import convert_brand, convert_currency, convert_event


class CUWebSpider(Spider):
    name = "cuweb"
    brand = "CU"

    custom_settings = {
        "USER_AGENT_TYPE": "desktop",
    }

    allowed_domains = ["cu.bgfretail.com"]
    base_url = "https://cu.bgfretail.com/index.do"
    list_base_url = "https://cu.bgfretail.com/product/productAjax.do"
    pb_list_base_url = "https://cu.bgfretail.com/product/pbAjax.do"
    detail_base_url = (
        "https://cu.bgfretail.com/product/view.do?category=product&gdIdx={gdIdx}"
    )
    # searchMainCategory == codeParent
    list_params = {
        "pageIndex": None,  # 1부터 시작
        "searchMainCategory": None,
        "searchSubCategory": "",  # Don't update - 전체 리스트에서 상세 페이지를 접근한다
        "listType": "0",  # Don't update
        "searchCondition": "setA",  # Don't update
        "searchUseYn": "N",  # Don't update
        "gdIdx": "0",  # Don't update
        "codeParent": None,
        "user_id": "",  # Don't update
        "search1": "",  # Don't update
        "search2": "",  # Don't update
        "searchKeyword": "",  # Don't update
    }
    # searchMainCategory 값
    list_category = {
        "fast-food": "10",
        "instant": "20",
        "snack": "30",
        "icecream": "40",
        "food": "50",
        "drink": "60",
        "household": "70",
    }

    pb_params = {
        "pageIndex": None,  # 1부터 시작
        "listType": "0",  # Don't update
        "searchCondition": "setA",  # Don't update
        "searchUseYn": "",  # Don't update
        "gdIdx": "0",  # Don't update
        "searchgubun": None,
        "search1": "",  # Don't update
        "search2": "",  # Don't update
        "searchKeyword": "",  # Don't update
    }

    # searchgubun 값
    pb_list_category = {
        "pb": "PBG",
        "cu": "CUG",
    }

    def start_requests(self) -> Request:
        # Get cookies
        yield Request(
            url=self.base_url,
            callback=self.form,
            cb_kwargs={"page": "1"},
            errback=self.errback,
            dont_filter=True,
        )

    def form(self, response: HtmlResponse, **kwargs) -> Request:
        # base list
        for category in self.list_category.values():
            params = self.list_params.copy()
            params["pageIndex"] = kwargs["page"]
            params["searchMainCategory"] = category
            params["codeParent"] = category
            yield FormRequest(
                url=self.list_base_url,
                formdata=params,
                callback=self.parse_list,
                cb_kwargs={"page": kwargs["page"]},
                dont_filter=True,
                errback=self.errback,
            )
        # pb list
        for category in self.pb_list_category.values():
            params = self.pb_params.copy()
            params["pageIndex"] = kwargs["page"]
            params["searchgubun"] = category
            yield FormRequest(
                url=self.pb_list_base_url,
                formdata=params,
                callback=self.parse_list,
                cb_kwargs={"page": kwargs["page"], "event": "MONOPOLY"},
                dont_filter=True,
                errback=self.errback,
            )

    def parse_list(self, response: HtmlResponse, **kwargs) -> Request:
        soup = BeautifulSoup(response.text, "html.parser")
        # id 추출
        # 1. prod_item
        if soup.select_one("a.prod_item") is not None:
            if soup.select_one("a.prod_item")["href"] == "#none":
                crawl_ids = list(
                    map(lambda x: x["onclick"], soup.select("a.prod_item"))
                )
            else:
                crawl_ids = list(map(lambda x: x["href"], soup.select("a.prod_item")))
        else:
            crawl_ids = soup.select("div.name")
            crawl_ids = list(map(lambda x: x["onclick"], crawl_ids))
        try:
            id_pattern = re.compile(r"view\((.+?)\)")
            crawl_ids = list(map(lambda x: id_pattern.search(x).group(1), crawl_ids))
        except Exception:
            self.logger.error(
                f"Failed to parse crawl ID: {response.url}\n{response.request.body}"
            )
            raise DropItem("Crawl ID doesn't exist")

        for crawl_id in crawl_ids:
            yield Request(
                url=self.detail_base_url.format(gdIdx=crawl_id),
                callback=self.parse,
                cb_kwargs={"crawl_id": crawl_id, "event": kwargs.get("event", None)},
                dont_filter=True,
                errback=self.errback,
            )

        if crawl_ids:
            # 현재 페이지에 상품이 있다면 다음 페이지로 이동. 현재 페이지에 상품이 없으면 마지막 페이지에 도달한 것이므로 종료
            page = str(int(kwargs["page"]) + 1)
            yield Request(
                url=self.base_url,
                callback=self.form,
                cb_kwargs={"page": page},
                dont_filter=True,
                errback=self.errback,
            )

    def parse(self, response: HtmlResponse, **kwargs) -> ItemType:
        tags = []
        events = []
        if kwargs["event"]:
            events.append(kwargs["event"])

        soup = BeautifulSoup(response.text, "lxml")
        detail = soup.select_one("div.prodDetail")
        if not detail:
            self.logger.debug("Fail to load detail page: {}".format(response.url))
            sleep(1)
            yield Request(
                url=response.url,
                callback=self.parse,
                cb_kwargs=kwargs,
                dont_filter=True,
                errback=self.errback,
                priority=1,
            )
            return

        product_img = detail.select_one("div.prodDetail-w > img")
        if product_img is None:
            raise DropItem("No product image")
        product_img = "https:" + product_img["src"]

        event_imgs = detail.select("div.prodDetail-w img")
        for event_img in event_imgs:
            if event_img["src"].startswith("/images"):
                events.append(event_img["alt"])

        product_name = detail.select_one("div.prodDetail-e > p.tit").text.strip()

        event_tags = detail.select("div.prodDetail-e > ul.prodTag > li")
        if event_tags:
            event_tags = list(map(lambda x: x.text.strip(), event_tags))
            events.extend(event_tags)

        product_info = detail.select_one("div.prodDetail-e > div.prodInfo")
        price = product_info.select_one("dd.prodPrice > p > span")
        if price is None:
            raise DropItem("Price is empty")
        price = float(re.sub(r"\D", "", price.text).strip())

        descriptions = detail.select("ul.prodExplain > li")
        if not descriptions:
            raise DropItem("Description doesn't exist")
        descriptions = list(map(lambda x: x.text.strip(), descriptions))
        description = "\n".join(descriptions)

        raw_tags = detail.select("#taglist > li")
        if not raw_tags:
            raise DropItem("tag doesn't exist")
        raw_tags = list(map(lambda x: x.text.strip(), raw_tags))
        tags.extend(raw_tags)

        # Build product

        product = ProductVO(
            crawled_info=CrawledInfoVO(
                spider=self.name,
                id=kwargs["crawl_id"],
                url=response.url,
                brand=convert_brand(self.brand),
            ),
            name=product_name,
            price=PriceVO(value=price, currency=convert_currency("KRW")),
            image=ImageVO(thumb=product_img),
            events=list(
                map(
                    lambda x: EventVO(
                        brand=convert_brand(self.brand), id=convert_event(x)
                    ),
                    events,
                )
            ),
            description=description,
            tags=tags,
        )
        yield product

    def errback(self, failure: Failure):
        # Retry if 403 Forbidden
        if failure.check(HttpError) and failure.value.response.status == 403:
            req: Request = failure.value.response.request.copy()
            req.dont_filter = True
            self.logger.error("403 Forbidden: {}. Retry after 5 sec".format(req.url))
            sleep(5)
            yield Request(
                self.base_url,
                callback=self.form,
                cb_kwargs=req.cb_kwargs,
                dont_filter=True,
            )
        else:
            self.logger.error(repr(failure))
