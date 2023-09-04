from argparse import ArgumentParser

from scrapy import cmdline


parser = ArgumentParser(
    prog="Pyoniverse Crawler",
    description="Crawl Convenience store",
    epilog="Created by YeongRo Yun",
)

parser.add_argument("--spider", type=str, required=True, help="Spider name")
parser.add_argument("--dev", action="store_true", help="Development mode")

if __name__ == "__main__":
    args = parser.parse_args()
    logfile = f"{args.spider}.log"
    loglevel = "DEBUG" if args.dev else "INFO"

    script = f"scrapy crawl --logfile {logfile} --loglevel {loglevel} {args.spider}"
    if args.dev:
        # Development mode - Don't save item to database
        cmdline.execute(script.split() + ["-s", "ITEM_PIPELINES={}"])
        pass
    else:
        cmdline.execute(script.split())
