import re, time, logging, json, csv
from collections import namedtuple, defaultdict
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from config import search_type, movie_list 


class Crawler:
    def __init__(self, **kwargs):
        self.ratings_site = 'https://www.reelgood.com'
        self.driver = webdriver.Firefox()
        self.default_timeout = 10
        self.wait = WebDriverWait(self.driver, self.default_timeout)
        self.movie_list = movie_list
        self.all_streaming_sites = defaultdict(int)
        self.all_streaming_sites["Movie"] = len(movie_list) + 1
        self.all_streaming_sites["None"] = len(movie_list)
        self.all_movies = []
        self.error_list = []
        self.start_index = kwargs.get('start_index')
        self.end_index = kwargs.get('end_index')
        self.StreamingPrice = namedtuple('StreamingPrice', 'site price')
        self.ErrorData = namedtuple('ErrorData', 'movie error')

    def get_all_movie_data(self):
        if not self.start_index:
            self.start_index = 0
        if not self.end_index:
            self.end_index = len(self.movie_list)
            
        for movie in self.movie_list[self.start_index:self.end_index]:
            # Initialize dict for storing movie data
            movie_info = {}

            # Get data for the given movie
            try:
                streaming_data_by_movie = self.get_movie_data(movie)

                # Check if there were no movies found
                if len(streaming_data_by_movie) == 1:
                    streaming_data_by_movie["None"] = "N/A"

            except Exception as e:
                error_data = self.ErrorData(movie, str(e))
                self.error_list.append(error_data)
                logging.exception(f'{str(e)} for "{movie}"')           
                continue
        
            # Add movie data to the full list
            self.all_movies.append(streaming_data_by_movie)
        
        self.driver.quit()

    def get_movie_data(self, movie):
        # Go to site
        self.driver.get(self.ratings_site)

        # Initialize list for streaming site data by movie
        streaming_data_by_movie = {"Movie": movie}

        # Search for movie then click on the correct movie
        logging.info(f'Searching for "{movie}"')
        self.movie_search(movie)
        time.sleep(1)

        # Wait for movie links to show up
        self.return_elements('xpath', self.movie_xpath)

        # Get "main" container & return movie link
        main = self.return_element('tag_name', 'main')
        movie_link = main.find_element_by_xpath(self.movie_xpath)

        # Movie found
        logging.info(f'Link found for "{movie}"')
        time.sleep(1)
        movie_link.click()
        
        # Get all the streaming data for each movie
        streaming_sites_table_header = self.return_element('xpath', "//h2[contains(text(), 'Where to Watch')]")
        streaming_sites_table_container = streaming_sites_table_header.find_element_by_xpath("./../../..")
        streaming_sites_table = streaming_sites_table_container.find_element_by_tag_name('nav')

        for streaming_site in streaming_sites_table.find_elements_by_xpath('./div'):
            try:
                streaming_price_data = streaming_site.find_elements_by_tag_name('span')
                streaming_site = streaming_price_data[0].get_attribute('innerHTML')
                streaming_site_price = streaming_price_data[1].get_attribute('innerHTML')
                self.all_streaming_sites[streaming_site] += 1
                streaming_price = self.StreamingPrice(streaming_site, streaming_site_price)
                streaming_data_by_movie[streaming_site] = streaming_site_price
            except Exception as e:
                error_data = self.ErrorData(movie, str(e))
                self.error_list.append(error_data)
                logging.exception(f'{str(e)} for "{movie}"')
                continue

        return streaming_data_by_movie

    def write_data(self):
        # open("all_movies.txt", "w").close()
        with open("all_movies.csv", "w") as f:
            sorted_sites = sorted(self.all_streaming_sites, key=self.all_streaming_sites.get, reverse=True)
            header = [key for key in sorted_sites]
            writer = csv.DictWriter(f, fieldnames=header)
            writer.writeheader()

            for movie in self.all_movies:
                writer.writerow(movie)
        
        open("errors.txt", "w").close()
        with open("errors.txt", "a") as f:
            for error in self.error_list:
                f.write(json.dumps(error))
                f.write('\n')
