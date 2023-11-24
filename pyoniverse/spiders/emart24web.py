import re
from pathlib import Path

from bs4 import BeautifulSoup, Tag
from scrapy import Request, Spider
from scrapy.exceptions import DropItem
from scrapy.http import HtmlResponse

from pyoniverse.items import CrawledInfoVO, EventVO, ImageVO, ItemType, PriceVO
from pyoniverse.items.product import ProductVO
from pyoniverse.items.utils import (
    convert_brand,
    convert_category,
    convert_currency,
    convert_event,
)


class Emart24WebSpider(Spider):
    """
    Mobile web spider for emart24.co.kr
    """

    name = "emart24web"
    brand = "emart24"
    allowed_domains = ["emart24.co.kr"]
    base_url = "http://m.emart24.co.kr"
    custom_settings = {
        "USER_AGENT_TYPE": "mobile",
        "LOG_FILE": f"{name}.log",
    }
    lists = {
        "event": "/goods/event",
        "PB": "/goods/pl",
        "Fresh": "/goods/ff",
    }
    event = {
        "1+1": "1+1",
        "2+1": "2+1",
        "3+1": "3+1",
        "세일": "DISCOUNT",
        "덤증정": "GIFT",
        "NEW": "NEW",
    }
    categories = {
        "도시락": {
            "category_seq": "8",
            "category": "LUNCH BOX",
        },
        "김밥": {
            "category_seq": "9",
            "category": "KIMBAP",
        },
        "햄버거": {"category_seq": "10", "category": "SANDWICH"},
        "주먹밥": {"category_seq": "41", "category": "KIMBAP"},
        "샌드위치": {"category_seq": "42", "category": "SANDWICH"},
        "즉석식": {"category_seq": "41", "category": "FOOD"},
    }
    pagination_url = base_url + "{list_path}?search=&category_seq={category_seq}&align="

    def start_requests(self):
        yield Request(url=self.base_url, callback=self.enter_main)

    def enter_main(self, response):
        for tab, path in self.lists.items():
            match tab:
                case "Fresh":
                    for value in self.categories.values():
                        category = value["category"]
                        category_seq = value["category_seq"]
                        yield Request(
                            url=self.pagination_url.format(
                                list_path=path,
                                category_seq=category_seq,
                            ),
                            callback=self.parse_list,
                            cb_kwargs={"tab": tab, "category": category},
                        )

                case _:
                    yield Request(
                        url=self.base_url + path,
                        callback=self.parse_list,
                        cb_kwargs={"tab": tab},
                    )

    def parse_list(self, response: HtmlResponse, **kwargs) -> Request:
        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.select("div.itemWrap")
        kwargs["url"] = response.url
        match kwargs["tab"]:
            case "event":
                for item in items:
                    yield from self.parse_item(item, **kwargs)
            case "PB":
                kwargs["event"] = "MONOPOLY"
                for item in items:
                    yield from self.parse_item(item, **kwargs)
            case "Fresh":
                for item in items:
                    yield from self.parse_item(item, **kwargs)
            case _:
                raise ValueError(f"Unknown list: {kwargs['list']!r}")

        next_page = soup.select_one(".nextButtons > .next > a")
        if next_page:
            yield Request(
                url=self.base_url + next_page["href"],
                callback=self.parse_list,
                cb_kwargs=kwargs,
            )

    def parse_item(self, item: Tag, **kwargs) -> ItemType:
        tags = item.select(".itemTit > span")
        events = []
        for tag in tags:
            if style := tag.get("style"):
                style = re.sub(r"\s+", "", style).strip().lower()
                if "opacity:0" in style:
                    continue
            events.append(tag.text.strip())
        events = [self.event[re.sub(r"\s+", "", e)] for e in events]
        if kwargs.get("event"):
            events.append(kwargs["event"])

        try:
            img = item.select_one(".itemImg > img")
            img = img["src"]
        except Exception:
            self.logger.error(f"Failed to get image URL: {item}")
            raise DropItem(f"Failed to get image URL: {item}")

        try:
            name = item.select_one(".itemtitle").text.strip()
        except Exception:
            self.logger.error(f"Failed to get name: {item}")
            raise DropItem(f"Failed to get name: {item}")

        try:
            discount_price = item.select_one(".priceOff").text.strip()
            discount_price = float(re.sub(r"\D", "", discount_price))
        except Exception:
            discount_price = None

        try:
            price = item.select_one(".price").text.strip()
            price = float(re.sub(r"\D", "", price))
        except Exception:
            self.logger.error(f"Failed to get price: {item}")
            raise DropItem(f"Failed to get price: {item}")

        if discount_price:
            # 할인 가격이 있으면, 할인 가격이 기본 가격이 됩니다.
            price, discount_price = discount_price, price

        product = ProductVO(
            crawled_info=CrawledInfoVO(
                spider=self.name,
                id=Path(img).stem,
                url=kwargs["url"],
                brand=convert_brand(self.brand),
            ),
            name=name,
            image=ImageVO(thumb=img),
            price=PriceVO(
                value=price,
                currency=convert_currency("KRW"),
                discounted_value=discount_price,
            ),
            events=[
                EventVO(brand=convert_brand(self.brand), id=convert_event(e))
                for e in events
            ],
            category=convert_category(kwargs.get("category"))
            if kwargs.get("category")
            else None,
        )
        yield product
