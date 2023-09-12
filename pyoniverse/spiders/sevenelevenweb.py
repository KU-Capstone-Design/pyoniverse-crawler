import re
from pathlib import Path
from time import sleep

from bs4 import BeautifulSoup
from scrapy import FormRequest, Request, Spider
from scrapy.exceptions import DropItem
from scrapy.http import HtmlResponse
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.python.failure import Failure

from pyoniverse.items import CrawledInfoVO, EventVO, ImageVO, ItemType, PriceVO
from pyoniverse.items.product import ProductVO
from pyoniverse.items.utils import (
    convert_brand,
    convert_category,
    convert_currency,
    convert_event,
)


class SevenElevenWebSpider(Spider):
    name = "sevenelevenweb"
    brand = "SEVEN ELEVEN"
    allowed_domains = ["www.7-eleven.co.kr"]
    base_url = "https://www.7-eleven.co.kr"

    tab = {
        "Fresh Food": {
            "main": "/product/bestdosirakList.asp",
            "pagination": "/product/dosirakNewMoreAjax.asp",
            "detail": "/product/bestdosirakView.asp",
        },
        "Cafe": {
            "main": "/product/7cafe.asp",
            "pagination": None,  # Cafe 는 pagination 없음
        },
        "Event": {
            "main": "/product/presentList.asp",
            "pagination": "/product/listMoreAjax.asp",
            "detail": "/product/presentView.asp",
        },
    }

    custom_settings = {
        # Fake User Agent Middleware 사용 X
        "DOWNLOADER_MIDDLEWARES": {
            # "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
            # 'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
            # "scrapy_fake_useragent.middleware.RandomUserAgentMiddleware": 400,
            # 'scrapy_fake_useragent.middleware.RetryUserAgentMiddleware': 401,
        }
    }

    def start_requests(self):
        # Get cookies
        yield Request(url=self.base_url, callback=self.enter_main, errback=self.errback)

    def enter_main(self, response: HtmlResponse, **kwargs) -> Request:
        for tab, url in self.tab.items():
            match tab:
                case "Fresh Food":
                    # 한번에 모든 데이터를 불러온다
                    ptabs = [
                        "noodle",  # 삼각김밥, 김밥,
                        "mini",  # 도시락, 조리면
                        "d_group",  # 샌드위치, 햄버거
                    ]
                    for ptab in ptabs:
                        form = {
                            "intPageSize": "100",
                            "pTab": ptab,
                        }
                        kwargs["size"] = "100"
                        kwargs["tab"] = tab
                        kwargs["ptab"] = ptab
                        yield FormRequest(
                            url=self.base_url + self.tab[tab]["pagination"],
                            formdata=form,
                            callback=self.parse_list,
                            errback=self.errback,
                            cb_kwargs=kwargs,
                            dont_filter=True,
                        )
                case "Cafe":
                    yield Request(
                        url=self.base_url + url["main"],
                        callback=self.parse_cafe,
                        errback=self.errback,
                        cb_kwargs={"tab": tab},
                        dont_filter=True,
                    )
                case "Event":
                    form = {
                        "cateCd1": "",
                        "cateNm1": "",
                        "cateCd2": "",
                        "cateNm2": "",
                        "cateCd3": "",
                        "cateNm3": "",
                        "pTab": None,
                        "pCd": "",
                        "intPageSize": "",
                    }
                    ptabs = [
                        "1",  # 1+1,
                        "2",  # 2+1,
                        "3",  # GIFT
                        "4",  # DISCOUNT
                        "5",  # PB
                        "8",  # NEW
                    ]

                    for ptab in ptabs:
                        form["pTab"] = ptab
                        kwargs["size"] = "10"
                        kwargs["tab"] = tab
                        kwargs["ptab"] = ptab
                        yield FormRequest(
                            url=self.base_url + self.tab[tab]["main"],
                            formdata=form,
                            callback=self.parse_list,
                            errback=self.errback,
                            cb_kwargs=kwargs,
                            dont_filter=True,
                        )
                case _:
                    raise ValueError("Invalid tab")

    def form_list(self, response: HtmlResponse, **kwargs) -> Request:
        soup = BeautifulSoup(response.text, "html.parser")
        data = soup.select_one("#actFrm > input")
        if data is None:
            self.logger.error("No data in {}".format(response.url))
            raise ValueError("No data in {}".format(response.url))
        data = data.attrs
        data = {data["name"]: data["value"]}
        yield FormRequest.from_response(
            response,
            formid="actFrm",
            formdata=data,
            callback=self.parse_list,
            errback=self.errback,
            cb_kwargs=kwargs,
        )

    def parse_list(self, response: HtmlResponse, **kwargs) -> Request:
        soup = BeautifulSoup(response.text, "html.parser")

        match kwargs["tab"]:
            case "Fresh Food":
                actual_size = soup.select_one("#listCnt")["value"]
                if int(kwargs["size"]) <= int(actual_size):
                    self.logger.debug(
                        "Size is not enough. {} <= {}".format(
                            kwargs["size"], actual_size
                        )
                    )
                    kwargs["size"] = str(int(kwargs["size"]) * 2)
                    form = {
                        "intPageSize": kwargs["size"],
                        "pTab": kwargs["ptab"],
                    }
                    yield FormRequest(
                        url=self.base_url + self.tab[kwargs["tab"]]["pagination"],
                        formdata=form,
                        callback=self.parse_list,
                        errback=self.errback,
                        cb_kwargs=kwargs,
                        dont_filter=True,
                    )
                    return
                else:
                    self.logger.debug(
                        "Size is enough. {} <= {}".format(kwargs["size"], actual_size)
                    )
                    items = soup.select(".dosirak_list > ul > li")[
                        1:-1
                    ]  # 처음과 마지막은 브랜드 & 페이징
                    for item in items:
                        # parse events
                        crawl_id, event_tags = self.extract_metainfos(item)

                        if kwargs["ptab"] == "d_group":
                            category = "SANDWICH"
                        elif kwargs["ptab"] == "noodle":
                            category = "KIMBAP"
                        else:
                            category = None

                        yield FormRequest(
                            url=self.base_url + self.tab[kwargs["tab"]]["detail"],
                            formdata={
                                "pCd": crawl_id,
                                "intPageSize": kwargs["size"],
                                "listCnt": actual_size,
                            },
                            callback=self.parse,
                            errback=self.errback,
                            cb_kwargs={
                                "events": event_tags,
                                "crawl_id": crawl_id,
                                "category": category,
                            },
                        )
            case "Event":
                items = soup.select("#listUl > li")[1:-1]
                form = soup.select("#actFrm > input")
                if not form:
                    self.logger.error("No form in {}".format(response.url))
                    raise ValueError("No form in {}".format(response.url))
                detail_form = {f["name"]: f["value"] for f in form}

                yield from self.parse_event_items(items, detail_form, **kwargs)

                list_form = {
                    "intPageSize": "10",
                    "intCurrPage": "2",
                    "cateCd1": "",
                    "cateCd2": "",
                    "cateCd3": "",
                    "pTab": kwargs["ptab"],
                }
                kwargs["list_form"] = list_form
                kwargs["detail_form"] = detail_form
                yield FormRequest(
                    url=self.base_url + self.tab[kwargs["tab"]]["pagination"],
                    formdata=list_form,
                    callback=self.event_list_more,
                    errback=self.errback,
                    cb_kwargs=kwargs,
                    dont_filter=True,
                )

            case _:
                raise ValueError("Invalid tab")

    def event_list_more(self, response: HtmlResponse, **kwargs) -> Request:
        soup = BeautifulSoup(response.text, "html.parser")
        cur_page = soup.select_one("#listPage")
        if not cur_page:
            self.logger.error("No page in {}".format(response.url))
            raise ValueError("No page in {}".format(response.url))
        cur_page = cur_page["value"]
        cur_size = soup.select_one("#listCnt")
        if not cur_size:
            self.logger.error("No size in {}".format(response.url))
            raise ValueError("No size in {}".format(response.url))
        cur_size = cur_size["value"]
        if int(cur_size) == 0:
            # No more items
            return
        items = soup.select("li")[:-1]
        kwargs["detail_form"]["intPageSize"] = kwargs["list_form"]["intPageSize"]
        kwargs["detail_form"]["listCnt"] = cur_size
        kwargs["detail_form"]["listPage"] = cur_page

        yield from self.parse_event_items(items, kwargs["detail_form"], **kwargs)

        kwargs["list_form"]["intCurrPage"] = cur_page

        yield FormRequest(
            url=self.base_url + self.tab[kwargs["tab"]]["pagination"],
            formdata=kwargs["list_form"],
            callback=self.event_list_more,
            errback=self.errback,
            cb_kwargs=kwargs,
            dont_filter=True,
        )

    def extract_metainfos(self, item):
        event_tags = item.select(".tag_list_01 > li")
        event_tags = [tag.text.strip() for tag in event_tags]
        tmp = []
        for tag in event_tags:
            if tag == "신상품":
                tmp.append("NEW")
            elif tag == "할인":
                tmp.append("DISCOUNT")
            elif tag == "PB":
                tmp.append("MONOPOLY")
            else:
                tmp.append(tag)
        event_tags = tmp
        crawl_id = item.select_one("a")["href"]
        crawl_id = re.search(r"fncGoView\('(.+)'\)", crawl_id).group(1)
        return crawl_id, event_tags

    def parse_event_items(self, items, detail_form, **kwargs):
        for item in items:
            crawl_id, event_tags = self.extract_metainfos(item)
            detail_form["pCd"] = crawl_id
            yield FormRequest(
                url=self.base_url + self.tab[kwargs["tab"]]["detail"],
                formdata=detail_form,
                callback=self.parse,
                errback=self.errback,
                cb_kwargs={
                    "events": event_tags,
                    "crawl_id": crawl_id,
                    "category": None,
                },
                dont_filter=True,
            )

    def parse(self, response: HtmlResponse, **kwargs) -> ItemType:
        soup = BeautifulSoup(response.text, "html.parser")
        try:
            name = soup.select_one(".tit_product_view").text.strip()
        except Exception:
            self.logger.error("Name not found")
            raise DropItem("Name not found")

        try:
            img = self.base_url + soup.select_one(".product_img img")["src"]
        except Exception:
            self.logger.error("Image not found")
            raise DropItem("Image not found")

        discounted_price = None
        try:
            if "DISCOUNT" in kwargs["events"]:
                discounted_price = soup.select_one(
                    ".product_price > strong"
                ).text.strip()
                price = soup.select_one(".product_price > del").text.strip()
                discounted_price = float(re.sub(r"\D", "", discounted_price))
                price = float(re.sub(r"\D", "", price))
            else:
                price = soup.select_one(".product_price > strong").text.strip()
                price = float(re.sub(r"\D", "", price))
        except Exception:
            self.logger.error("Price not found")
            raise DropItem("Price not found")

        # Build Item
        product = ProductVO(
            crawled_info=CrawledInfoVO(
                spider=self.name,
                id=kwargs["crawl_id"],
                url=response.url,
            ),
            category=convert_category(kwargs["category"])
            if kwargs.get("category")
            else None,
            name=name,
            price=PriceVO(value=price, currency=convert_currency("KRW")),
            discounted_price=discounted_price,
            image=ImageVO(thumb=img),
            events=[
                EventVO(brand=convert_brand(self.brand), id=convert_event(e))
                for e in kwargs["events"]
            ],
        )
        yield product

    def parse_cafe(self, response: HtmlResponse, **kwargs) -> ItemType:
        soup = BeautifulSoup(response.text, "html.parser")
        menu = soup.select_one(".cafeMenu")
        items = menu.select("li")
        for item in items:
            try:
                name = item.select_one(".tit").text.strip()
            except Exception:
                self.logger.error("Name doesn't exist")
                raise DropItem("Name doesn't exist")

            try:
                img = self.base_url + item.select_one("img")["src"]
            except Exception:
                self.logger.error("Image doesn't exist")
                raise DropItem("Image doesn't exist")

            try:
                price = item.select_one(".price").text.strip()
                price = float(re.sub(r"\D", "", price))
            except Exception:
                self.logger.error("Price doesn't exist")
                raise DropItem("Price doesn't exist")

            product = ProductVO(
                crawled_info=CrawledInfoVO(
                    spider=self.name,
                    id=Path(img).stem,
                    url=response.url,
                ),
                name=name,
                image=ImageVO(thumb=img),
                price=PriceVO(value=price, currency=convert_currency("KRW")),
                category=convert_category("DRINK"),
            )
            yield product

    def errback(self, failure: Failure):
        # Retry if 403 Forbidden
        if failure.check(HttpError) and failure.value.response.status == 403:
            req: Request = failure.value.response.request.copy()
            req.dont_filter = True
            self.logger.error("403 Forbidden: {}. Retry after 5 sec".format(req.url))
            sleep(5)
            yield req
        else:
            self.logger.error(repr(failure))
