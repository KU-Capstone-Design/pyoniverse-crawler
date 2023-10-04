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
        AllRunner.run(loglevel=loglevel, stage=args.stage)
