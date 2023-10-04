import re
from pathlib import Path

from bs4 import BeautifulSoup, Tag
from scrapy import Request, Spider
from scrapy.exceptions import DropItem
from scrapy.http import HtmlResponse

from pyoniverse.items import CrawledInfoVO, EventVO, ImageVO, PriceVO
from pyoniverse.items.product import ProductVO
from pyoniverse.items.utils import convert_brand, convert_currency, convert_event


class CspaceWebSpider(Spider):
    name = "cspaceweb"
    brand = "cspace"

    allowed_domains = ["cspace.co.kr"]

    custom_settings = {
        "USER_AGENT_TYPE": "desktop",
        "download_delay": 5,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        "LOG_FILE": f"{name}.log",
    }

    base_url = "https://www.cspace.co.kr"

    product_list_url = "https://www.cspace.co.kr/service/product.html"

    events = {
        "sale": "DISCOUNT",
        "onePlus": "1+1",
        "twoPlus": "2+1",
    }

    def start_requests(self):
        yield Request(url=self.base_url, callback=self.enter, dont_filter=True)

    def enter(self, response: HtmlResponse) -> Request:
        yield Request(
            url=self.product_list_url, callback=self.parse_list, dont_filter=True
        )

    def parse_list(self, response: HtmlResponse) -> Request:
        soup = BeautifulSoup(response.text, "html.parser")

        items = soup.select("ul.box > li")
        for item in items:
            yield from self.parse_product(item, response.url)

        pagination = soup.select_one(".pagination.pc")
        cur_page = pagination.select_one("a.active").parent  # li tag
        if next_page := cur_page.find_next_sibling("li"):
            if next_page.select_one("a")["href"] != "#void":
                self.logger.info(f"Next page: {next_page.select_one('a')['href']}")
                yield Request(
                    url=self.base_url + next_page.select_one("a")["href"],
                    callback=self.parse_list,
                )

    def parse_product(self, item: Tag, url: str) -> Request:
        events = item["class"]
        try:
            events = [self.events[event] for event in events if event in self.events]
        except KeyError:
            raise DropItem(f"Unknown event: {events} in {item}, {url}")

        if img := item.select_one("img"):
            img_url = img["src"]
            if "no_img" in img_url:
                img_url = None
            else:
                img_url = self.base_url + img_url
        else:
            img_url = None

        try:
            name = item.select_one("dt").text.strip()
        except Exception:
            raise DropItem(f"Unknown name in {item}, {url}")

        try:
            price = item.select_one("dd").text.strip()
            price = float(re.sub(r"\D", "", price))
        except Exception:
            raise DropItem(f"Unknown price in {item}, {url}")

        if img_url is not None:
            crawl_id = str(Path("/".join(img_url.split("/")[-2:])).with_suffix(""))
            if crawl_id.startswith("product/"):
                crawl_id = crawl_id[len("product/") :]
        else:
            crawl_id = name

        product = ProductVO(
            crawled_info=CrawledInfoVO(
                spider=self.name,
                # 이름 외 다른 고유값이 없음(이미지도 없을 수 있기 때문에)
                id=crawl_id,
                url=url,
                brand=convert_brand(self.brand),
            ),
            name=name,
            price=PriceVO(
                value=price,
                currency=convert_currency("KRW"),
                discounted_value=price if "DISCOUNT" in events else None,
            ),
            image=ImageVO(thumb=img_url),
            events=[
                EventVO(brand=convert_brand(self.brand), id=convert_event(event))
                for event in events
            ],
        )
        yield product
