import argparse
from datetime import datetime
import logging
from helpers import Crawler

parser = argparse.ArgumentParser()
parser.add_argument('--start_index', help='The start index of the movie list you would like to pull', type=int)
parser.add_argument('--end_index', help='The end index of the movie list you would like to pull', type=int)
args = parser.parse_args()
start_index = args.start_index
end_index = args.end_index

logging.basicConfig(
    # filename=f'./logs/movie_crawler_log-{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}.log',
    filename=f'./logs/movie_crawler_log-{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}.log',
    format='%(asctime)s: %(levelname)s - %(name)s - %(module)s %(funcName)s, line %(lineno)d: %(message)s',
    datefmt='%m/%d/%Y %H:%M:%S',
    level=logging.INFO
)


if __name__ == "__main__":
    crawler = Crawler(start_index=start_index, end_index=end_index)
    crawler.get_all_movie_data()
    crawler.write_data()