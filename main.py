from argparse import ArgumentParser

import dotenv
import nest_asyncio

from pyoniverse.db.client import DBClient


parser = ArgumentParser(
    prog="Pyoniverse Crawler",
    description="Crawl Convenience store",
    epilog="Created by YeongRo Yun",
)

parser.add_argument(
    "spider", type=str, help="Spider name. If spider==all then Run all spiders"
)
parser.add_argument(
    "--stage", type=str, default="test", choices=["dev", "prod", "test"], required=True
)
parser.add_argument(
    "--clear_db",
    action="store_true",
    help="crawling_* DB 데이터 삭제. ETL Pipeline 상에서 동작할 때 사용. " "spider=all 이어야 한다",
)

nest_asyncio.apply()
dotenv.load_dotenv()
if __name__ == "__main__":
    from pyoniverse.runners.all_runner import AllRunner
    from pyoniverse.runners.single_runner import SingleRunner

    args = parser.parse_args()
    if args.stage in {"dev", "test"}:
        loglevel = "DEBUG"
    else:
        loglevel = "INFO"

    if args.spider != "all":
        SingleRunner.run(spider=args.spider, loglevel=loglevel, stage=args.stage)
    else:
        if args.clear_db:
            client = DBClient.instance()
            client.clear()
        AllRunner.run(loglevel=loglevel, stage=args.stage)
