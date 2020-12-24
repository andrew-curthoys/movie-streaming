import re, time, logging, json
from collections import namedtuple
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
                streaming_sites_by_movie = self.get_movie_data(movie)
            except Exception as e:
                error_data = self.ErrorData(movie, str(e))
                self.error_list.append(error_data)
                logging.exception(f'{str(e)} for "{movie}"')           
                continue
            
            # Add move streaming data to dictionary for the given movie
            movie_info[movie] = streaming_sites_by_movie
        
            # Add movie data to the full list
            self.all_movies.append(movie_info)
        
        self.driver.quit()

    def get_movie_data(self, movie):
        # Go to site
        self.driver.get(self.ratings_site)

        # Initialize list for streaming site data by movie
        streaming_data_by_movie = []

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
        streaming_sites_table_header = self.return_element('xpath', "//*[contains(text(), 'Where to Watch')]")
        streaming_sites_table_container = streaming_sites_table_header.find_element_by_xpath("./../../..")
        streaming_sites_table = streaming_sites_table_container.find_element_by_tag_name('nav')

        for streaming_site in streaming_sites_table.find_elements_by_xpath('./div'):
            try:
                streaming_price_data = streaming_site.find_elements_by_tag_name('span')
                streaming_site = streaming_price_data[0].get_attribute('innerHTML')
                streaming_site_price = streaming_price_data[1].get_attribute('innerHTML')
                streaming_price = self.StreamingPrice(streaming_site, streaming_site_price)
                streaming_data_by_movie.append(streaming_price)

            except Exception as e:
                error_data = self.ErrorData(movie, str(e))
                self.error_list.append(error_data)
                logging.exception(f'{str(e)} for "{movie}"')
                continue

        return streaming_data_by_movie

    def write_data(self):
        open("all_movies.txt", "w").close()
        with open("all_movies.txt", "a") as f:
            for movie in self.all_movies:
                f.write(json.dumps(movie))
                f.write('\n')
        open("errors.txt", "w").close()
        with open("errors.txt", "a") as f:
            for error in self.error_list:
                f.write(json.dumps(error))
                f.write('\n')

    def movie_search(self, movie_name):
        movie_xpath_name = movie_name.lower().replace(' ', '_')
        movie_xpath_name = re.sub(r'[^\w]', '', movie_xpath_name)
        movie_xpath_name = movie_xpath_name.lower().replace('_', '-')
        self.movie_xpath = f"//a[contains(@href, '{movie_xpath_name}')]"
        self.driver.get('https://reelgood.com')
        searchbar = self.return_element('id', 'searchbox')
        searchbar.clear()
        searchbar.send_keys(movie_name)
        searchbar.submit()

    def return_element(self, element_type, element_name, **kwargs):
        timeout = kwargs.get('timeout')
        if timeout:
            elem = WebDriverWait(self.driver, timeout).until(ec.presence_of_element_located((search_type[element_type], element_name)))
        else:
            elem = WebDriverWait(self.driver, self.default_timeout).until(ec.presence_of_element_located((search_type[element_type], element_name)))
        return elem

    def return_elements(self, element_type, element_name, **kwargs):
        timeout = kwargs.get('timeout')
        if timeout:
            elem = WebDriverWait(self.driver, timeout).until(ec.presence_of_element_located((search_type[element_type], element_name)))
        else:
            elem = WebDriverWait(self.driver, self.default_timeout).until(ec.presence_of_element_located((search_type[element_type], element_name)))
        return elem
