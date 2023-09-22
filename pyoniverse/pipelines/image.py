import logging
import re
import warnings
from io import BytesIO
from pathlib import Path
from typing import List

from scrapy import Request
from scrapy.exceptions import ScrapyDeprecationWarning
from scrapy.pipelines.files import S3FilesStore
from scrapy.pipelines.images import ImagesPipeline
from scrapy.utils.misc import md5sum
from scrapy.utils.python import get_func_args

from pyoniverse.items.event import BrandEventVO
from pyoniverse.items.product import ProductVO


class S3ImagePipeline(ImagesPipeline):
    """
    S3에 이미지를 저장한다.
    """

    stage: str = None
    logger: logging.Logger = None

    @classmethod
    def from_settings(cls, settings):
        stage = settings["STAGE"]
        pipeline = super().from_settings(settings)
        pipeline.stage = stage
        return pipeline

    def open_spider(self, spider):
        self.logger = spider.logger
        return super().open_spider(spider)

    def get_media_requests(self, item: ProductVO, info):
        """
        :param item: Product | Event
        :param info:
        :return: Request for image
        """
        if item.image.thumb:
            yield Request(item.image.thumb)
        for url in item.image.others:
            yield Request(url)

    def file_path(self, request, response=None, info=None, *, item: ProductVO = None):
        path = super().file_path(request, response, info, item=item)
        if isinstance(item, ProductVO):
            prefix = "products"
        elif isinstance(item, BrandEventVO):
            prefix = "events"
        else:
            raise ValueError("Invalid item type")
        path = re.sub(r"^full", rf"{prefix}", path)
        return path

    def item_completed(self, results: List[dict], item: ProductVO, info):
        """
        self.store: S3FilesStore
        """
        store: S3FilesStore = self.store
        for ok, value in results:
            if ok:
                # Webp 로 변환
                path = Path(value["path"]).with_suffix(".webp")
                if store.prefix:
                    url = f"s3://{store.bucket}/{store.prefix}/{path}"
                else:
                    url = f"s3://{store.bucket}/{path}"
                if value["url"] == item.image.thumb:
                    item.image.thumb = url
                else:
                    item.image.others = [
                        o if o != value["url"] else url for o in item.image.others
                    ]
            else:
                self.logger.warning(f"Image download failed: {str(value)}\n{item}")
        if item.image.thumb and not item.image.thumb.startswith("s3"):
            item.image.thumb = None
        item.image.others = [o for o in item.image.others if not o.startswith("s3")]
        return item

    # Webp 저장을 위한 Overrides
    def convert_image(self, image, size=None, response_body=None):
        """
        webp Image 로 저장한다.
        """
        if response_body is None:
            warnings.warn(
                f"{self.__class__.__name__}.convert_image() method called in a deprecated way, "
                "method called without response_body argument.",
                category=ScrapyDeprecationWarning,
                stacklevel=2,
            )

        if image.format in ("PNG", "WEBP") and image.mode == "RGBA":
            background = self._Image.new("RGBA", image.size, (255, 255, 255))
            background.paste(image, image)
            image = background.convert("RGB")
        elif image.mode == "P":
            image = image.convert("RGBA")
            background = self._Image.new("RGBA", image.size, (255, 255, 255))
            background.paste(image, image)
            image = background.convert("RGB")
        elif image.mode != "RGB":
            image = image.convert("RGB")

        if size:
            image = image.copy()
            try:
                # Image.Resampling.LANCZOS was added in Pillow 9.1.0
                # remove this try except block,
                # when updating the minimum requirements for Pillow.
                resampling_filter = self._Image.Resampling.LANCZOS
            except AttributeError:
                resampling_filter = self._Image.ANTIALIAS
            image.thumbnail(size, resampling_filter)
        # Webp 로 변환
        buf = BytesIO()
        image.save(buf, format="webp")
        return image, buf

    def get_images(self, response, request, info, *, item=None):
        path = self.file_path(request, response=response, info=info, item=item)
        # Convert format to webp
        path = Path(path).with_suffix(".webp")
        orig_image = self._Image.open(BytesIO(response.body))

        width, height = orig_image.size
        if width < self.min_width or height < self.min_height:
            orig_image = orig_image.resize(
                (max(width, self.min_width), max(height, self.min_height)),
                reducing_gap=3.0,
            )
            self.logger.warning(
                f"Image too small "
                f"({width}x{height} < "
                f"{self.min_width}x{self.min_height}), "
                f"resized to ({orig_image.width}x{orig_image.height})"
            )
        # webp maximum image size check
        max_width, max_height = 16383, 16383
        if orig_image.width > max_width or orig_image.height > max_height:
            orig_image = orig_image.resize(
                (min(orig_image.width, max_width), min(orig_image.height, max_height)),
                reducing_gap=3.0,
            )
            self.logger.warning(
                f"Image too large "
                f"({width}x{height} > "
                f"{max_width}x{max_height}), "
                f"resized to ({orig_image.width}x{orig_image.height})"
            )
        if self._deprecated_convert_image is None:
            self._deprecated_convert_image = "response_body" not in get_func_args(
                self.convert_image
            )
            if self._deprecated_convert_image:
                warnings.warn(
                    f"{self.__class__.__name__}.convert_image() method overridden in a deprecated way, "
                    "overridden method does not accept response_body argument.",
                    category=ScrapyDeprecationWarning,
                )

        if self._deprecated_convert_image:
            image, buf = self.convert_image(orig_image)
        else:
            image, buf = self.convert_image(
                orig_image, response_body=BytesIO(response.body)
            )
        yield path, image, buf

        for thumb_id, size in self.thumbs.items():
            thumb_path = self.thumb_path(
                request, thumb_id, response=response, info=info, item=item
            )
            # Convert format to webp
            thumb_path = Path(thumb_path).with_suffix(".webp")
            if self._deprecated_convert_image:
                thumb_image, thumb_buf = self.convert_image(image, size)
            else:
                thumb_image, thumb_buf = self.convert_image(image, size, buf)
            yield thumb_path, thumb_image, thumb_buf

    def image_downloaded(self, response, request, info, *, item=None):
        checksum = None
        for path, image, buf in self.get_images(response, request, info, item=item):
            if checksum is None:
                buf.seek(0)
                checksum = md5sum(buf)
            width, height = image.size

            # Image Size 저장
            url_path = Path(request.url)
            if item.image.thumb and url_path == Path(item.image.thumb):
                item.image.size["thumb"] = {"width": width, "height": height}
            else:
                # 같은 우선순위끼리는 FIFO로 저장되므로, 순서가 보장됨
                if "others" not in item.image.size:
                    item.image.size["others"] = []
                item.image.size["others"].append(
                    {
                        "width": width,
                        "height": height,
                    }
                )
            if self.stage != "test":
                self.store.persist_file(
                    path,
                    buf,
                    info,
                    meta={"width": width, "height": height},
                    # Webp Type 으로 저장
                    headers={"Content-Type": "image/webp"},
                )
            else:
                self.logger.debug("Test mode - Image not saved")
        return checksum
