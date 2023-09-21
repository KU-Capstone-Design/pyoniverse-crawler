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
from pyoniverse.items.utils import (
    convert_brand,
    convert_category,
    convert_currency,
    convert_event,
)


class Gs25WebSpider(Spider):
    name = "gs25web"
    brand = "GS25"

    custom_settings = {
        "USER_AGENT_TYPE": "desktop",
    }

    allowed_domains = ["gs25.gsretail.com"]
    base_url = "http://gs25.gsretail.com"

    start_urls = {
        "event": "http://gs25.gsretail.com/gscvs/ko/products/event-goods",
        "youus": "http://gs25.gsretail.com/gscvs/ko/products/youus-main",
    }

    search_urls = {
        "event": "http://gs25.gsretail.com/gscvs/ko/products/event-goods-search",
        "youus": "http://gs25.gsretail.com/products/youus-freshfoodDetail-search",
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

    def start_requests(self):
        for key, url in self.start_urls.items():
            if key == "event":
                # Page 는 1부터 시작합니다.
                yield Request(
                    url,
                    callback=self.parse_event_home,
                    headers=self.headers,
                    cb_kwargs={"type": "event", "page": 1},
                )
            elif key == "youus":
                yield Request(
                    url,
                    callback=self.parse_youus_home,
                    headers=self.headers,
                    cb_kwargs={"type": "youus", "page": 1},
                )
            else:
                raise RuntimeError("Unknown key: {}".format(key))

    def parse_event_home(self, response: HtmlResponse, **kwargs) -> ItemType:
        """
        이벤트 상품 목록을 가져옵니다.
        - 1+1
        - 2+1
        - 덤증정
        """
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

    def parse_youus_home(self, response: HtmlResponse, **kwargs) -> ItemType:
        """
        유어스 상품 목록을 가져옵니다.
        - Fresh Food
        - PB 상품
        """
        soup = BeautifulSoup(response.body, "html.parser")
        form = soup.select_one("#CSRFForm")
        if not form:
            raise RuntimeError("Can't find event post action")

        csrf_token = form.select_one("input")["value"]
        req_url = self.search_urls["youus"]
        query = "CSRFToken={}".format(csrf_token)

        if "srv_food_ck" not in kwargs:
            search_food_ck_map = {
                "FreshFoodKey": [
                    "productLunch",  # 도시락
                    "productRice",  # 김밥류
                    "productBurger",  # 버거/샌드위치
                    "productSnack",  # 간편식
                ],
                "DifferentServiceKey": [
                    "productDrink",  # 음료
                    "productMilk",  # 유제품
                    "productCookie",  # 과자/간식
                    "productRamen",  # 라면/가공식품
                    "productGoods",  # 생활용품
                ],
            }

            for srv_food_ck, search_product_list in search_food_ck_map.items():
                for search_product in search_product_list:
                    form_data = {
                        "pageNum": str(kwargs["page"]),
                        "pageSize": "16",
                        "searchWord": "",
                        "searchHPrice": "",
                        "searchTPrice": "",
                        "searchSrvFoodCK": srv_food_ck,
                        "searchSort": "searchALLSort",
                        "searchProduct": search_product,
                    }

                    header = self.headers.copy()
                    kwargs.update(
                        {"srv_food_ck": srv_food_ck, "search_product": search_product}
                    )
                    yield FormRequest(
                        url=f"{req_url}?{query}",
                        callback=self.parse_youus,
                        errback=self.errback,
                        formdata=form_data,
                        cb_kwargs=kwargs,
                        headers=header,
                        dont_filter=True,
                    )
        else:
            yield FormRequest(
                url=f"{req_url}?{query}",
                callback=self.parse_youus,
                errback=self.errback,
                formdata={
                    "pageNum": str(kwargs["page"]),
                    "pageSize": "16",
                    "searchWord": "",
                    "searchHPrice": "",
                    "searchTPrice": "",
                    "searchSrvFoodCK": kwargs["srv_food_ck"],
                    "searchSort": "searchALLSort",
                    "searchProduct": kwargs["search_product"],
                },
                cb_kwargs=kwargs,
                headers=self.headers,
                dont_filter=True,
            )

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
                    spider=self.name,
                    url=response.url,
                    id=product_id,
                    brand=convert_brand(self.brand),
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

    def parse_youus(self, response: HtmlResponse, **kwargs) -> ItemType:
        body = response.json()
        if isinstance(body, str):
            body = json.loads(body)
        pagination = body["SubPageListPagination"]
        results = body["SubPageListData"]

        if not results:
            return

        for result in results:
            result = {k: v for k, v in result.items() if not k.endswith("Old")}
            product_name = result["goodsNm"]
            product_price = float(result["price"])
            product_img = result.get("attFileNm")
            if not product_img:
                raise DropItem("No image: {}".format(product_name))
            # product_id = image_path 의 마지막 부분을 id 로 사용합니다.
            product_id = Path(product_img).stem

            events = []
            if result.get("isNew", "F") == "T":
                events.append("NEW")
            if kwargs["srv_food_ck"] == "DifferentServiceKey":
                events.append("MONOPOLY")

            category = None
            if kwargs["srv_food_ck"] == "FreshFoodKey":
                match kwargs["search_product"]:
                    case "productLunch":
                        category = "LUNCH BOX"
                    case "productRice":
                        category = "KIMBAP"
                    case "productBurger":
                        category = "SANDWICH"
                    case "productSnack":
                        if "샐만사" in product_name or "샐러드" in product_name:
                            category = "SALAD"
                        else:
                            category = "FOOD"
                    case _:
                        category = None
            elif kwargs["srv_food_ck"] == "DifferentServiceKey":
                match kwargs["search_product"]:
                    case "productDrink":
                        category = "DRINK"
                    case "productMilk":
                        if "베이글" in product_name:
                            category = "BREAD"
                        elif "ML" in product_name.upper():
                            category = "DRINK"
                        else:
                            category = "FOOD"
                    case "productCookie":
                        if (
                            "수박바" in product_name
                            or "폴라포" in product_name
                            or "파르페" in product_name
                            or "쿨샷스포츠" in product_name
                            or "빵빠레"
                        ):
                            category = "ICE CREAM"
                        elif (
                            "쿠키" in product_name
                            or "약과" in product_name
                            or "칩" in product_name
                            or "과자" in product_name
                            or "스낵" in product_name
                            or "젤리" in product_name
                            or "스틱" in product_name
                            or "초코콘" in product_name
                            or "딸기별" in product_name
                            or "오감자" in product_name
                            or "푸딩" in product_name
                            or "초코렛타" in product_name
                            or "나쵸" in product_name
                            or "꾸이깡" in product_name
                            or "프레첼" in product_name
                            or "팝콘" in product_name
                            or "초코볼" in product_name
                            or "누네띠네" in product_name
                            or "자일리톨" in product_name
                        ):
                            category = "SNACK"
                        elif (
                            "티라미수" in product_name
                            or "케익" in product_name
                            or "바닐라슈" in product_name
                            or "모찌롤" in product_name
                        ):
                            category = "BREAD"
                        else:
                            category = "FOOD"

                    case "productRamen":
                        if (
                            product_name.endswith("컵")
                            or product_name.endswith("찌개")
                            or product_name.endswith("탕")
                            or product_name.endswith("밥")
                        ):
                            category = "FOOD"
                        else:
                            category = "CUP NOODLE"
                    case "productGoods":
                        category = "HOUSEHOLD GOODS"
                    case _:
                        category = None
            else:
                raise RuntimeError(
                    "Unknown srv_food_ck: {}".format(kwargs["srv_food_ck"])
                )

            product: ProductVO = ProductVO(
                crawled_info=CrawledInfoVO(
                    spider=self.name,
                    url=response.url,
                    id=product_id,
                    brand=convert_brand(self.brand),
                ),
                category=convert_category(category) if category else None,
                name=product_name,
                price=PriceVO(value=product_price, currency=convert_currency("KRW")),
                image=ImageVO(thumb=product_img),
                events=[
                    EventVO(
                        id=convert_event(event_type), brand=convert_brand(self.brand)
                    )
                    for event_type in events
                ],
            )
            yield product

        current_page = int(kwargs["page"])
        self.logger.info(f"Next page: {current_page + 1}/{pagination['numberOfPages']}")
        kwargs["page"] = current_page + 1
        yield Request(
            self.start_urls["event"],
            callback=self.parse_youus_home,
            headers=self.headers,
            cb_kwargs=kwargs,
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
                        callback=self.parse_youus_home,
                        headers=self.headers,
                        cb_kwargs=req.cb_kwargs,
                        dont_filter=True,
                    )
                case _:
                    raise RuntimeError("Unknown type: {}".format(req.cb_kwargs["type"]))
        else:
            self.logger.error(repr(failure))
