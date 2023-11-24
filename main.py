from argparse import ArgumentParser

import dotenv
import nest_asyncio


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
args = parser.parse_args()
if __name__ == "__main__":
    from pyoniverse.engine import Engine

    engine = Engine(stage=args.stage, spider=args.spider, clear_db=args.clear_db)
    res = engine.run()
    if res:
        exit(0)
    else:
        exit(1)  # Failed
