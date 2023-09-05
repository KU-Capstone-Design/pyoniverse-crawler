import os
from argparse import ArgumentParser

import dotenv
import nest_asyncio
from scrapy import cmdline


parser = ArgumentParser(
    prog="Pyoniverse Crawler",
    description="Crawl Convenience store",
    epilog="Created by YeongRo Yun",
)

parser.add_argument("--spider", type=str, required=True, help="Spider name")
parser.add_argument("--test", action="store_true", help="Development mode")

nest_asyncio.apply()
dotenv.load_dotenv()
if __name__ == "__main__":
    args = parser.parse_args()
    logfile = f"{args.spider}.log"
    if args.test:
        # Test mode - Override stage environment variable
        os.environ["STAGE"] = "test"

    if os.getenv("STAGE") in {"dev", "test"}:
        loglevel = "DEBUG"
    else:
        loglevel = "INFO"
    script = f"scrapy crawl --logfile {logfile} --loglevel {loglevel} {args.spider}"
    if args.test:
        cmdline.execute(script.split())
    else:
        # .dotenv 파일을 Github에 올리지 않기 때문에, GitAction Secret에 저장된 환경변수로 .dotenv 파일을 생성
        cmdline.execute(script.split())
