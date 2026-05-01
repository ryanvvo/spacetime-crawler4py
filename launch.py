from configparser import ConfigParser
from argparse import ArgumentParser

from utils.server_registration import get_cache_server
from utils.config import Config
from crawler import Crawler
import shelve
from scraper import update_shelf
SHELF_PATH = "scraper.shelve"
OUTPUT_PATH = "output.txt"

def main(config_file, restart):
    cparser = ConfigParser()
    cparser.read(config_file)
    config = Config(cparser)
    config.cache_server = get_cache_server(config, restart)
    crawler = Crawler(config, restart)
    if restart:
        with shelve.open(SHELF_PATH) as db:
            print("Clearing", SHELF_PATH, "...")
            db.clear()
        with open(OUTPUT_PATH, "w") as file:
            print("Clearing", OUTPUT_PATH, "...")
            pass
        update_shelf()
    crawler.start()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--restart", action="store_true", default=False)
    parser.add_argument("--config_file", type=str, default="config.ini")
    args = parser.parse_args()
    main(args.config_file, args.restart)
