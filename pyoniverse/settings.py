# Scrapy settings for pyoniverse project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import os


BOT_NAME = "pyoniverse"

SPIDER_MODULES = ["pyoniverse.spiders"]
NEWSPIDER_MODULE = "pyoniverse.spiders"

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = "pyoniverse (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
# CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 1
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
# CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
# COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
# }

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    "pyoniverse.middlewares.PyoniverseSpiderMiddleware": 543,
# }

# scrapy-fake-useragent 설정(Recommended 를 따름) - https://pypi.org/project/scrapy-fake-useragent/
DOWNLOADER_MIDDLEWARES = {
    "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
    # 'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
    "scrapy_fake_useragent.middleware.RandomUserAgentMiddleware": 400,
    # 'scrapy_fake_useragent.middleware.RetryUserAgentMiddleware': 401,
}

FAKEUSERAGENT_PROVIDERS = [
    "scrapy_fake_useragent.providers.FakeUserAgentProvider",  # this is the first provider we'll try
    "scrapy_fake_useragent.providers.FakerProvider",
    "scrapy_fake_useragent.providers.FixedUserAgentProvider",  # fall back to USER_AGENT value
]
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)"

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
# }

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    "pyoniverse.pipelines.validator.ValidationPipeline": 100,
    "pyoniverse.pipelines.image.S3ImagePipeline": 200,
    "pyoniverse.pipelines.db.MongoDBPipeline": 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
# AUTOTHROTTLE_ENABLED = True
# The initial download delay
# AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = "httpcache"
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

# Debugging
# TODO : Change Log format

# Output Items
FEEDS = {
    "debug.json": {
        "format": "json",
        "store_empty": False,
        "indent": 4,
        "overwrite": True,
    },
}

# Secrets - .env
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")
STAGE = os.getenv("STAGE")

# LOG
LOG_FILE_APPEND = False

# Image
IMAGES_STORE = "s3://pyoniverse-image/"  # bucket, prefix = IMAGE_STORE[5:].split("/")
IMAGES_MIN_HEIGHT = 360
IMAGES_MIN_WIDTH = 360
