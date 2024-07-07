import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.exceptions import CloseSpider
from typing import List
import logging
import random
import os
from concurrent.futures import ThreadPoolExecutor
import requests






class AproxSpiderSpider(CrawlSpider):
    name = "aprox-spider"
    

    custom_settings = {
        'DOWNLOAD_DELAY': 0.01,  # add download delay of 1 second
        'CONCURRENT_REQUESTS': 20, # 128,  # Adjust the concurrency level as needed
        'CONCURRENT_REQUESTS_PER_DOMAIN' : 2_000, # for the current limit this must be so high
        'RETRY_TIMES': 0,  # Number of times to retry a failed request
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 443],  # HTTP status codes to retry
        'ROBOTSTXT_OBEY' : False,
        #   ------ closing spider aftre 50 items -------
        #'CLOSESPIDER_ITEMCOUNT': 100,
    }


    #allowed_domains = ["example.com"]

    # Predicts the url ending for the spider
    def predicting_url(self, url : str) -> List[str]:

        ret_list = [url]

        for i in range(1, 3250):
            ret_list.append(url + "?start=" + str(i*25))
        
        return ret_list

    # Generate the start URLs that the spider crawls
    def start_url_generator(self) -> list[tuple[str, str]]:
        category_list = ["nyomtato-patron-toner-c3138/",
                        "szamitogep-periferia-c3107/"]
        
        category_names = ["nyomtato-patron-toner",
                        "szamitogep-periferia"]

        base_url = "https://www.arukereso.hu/"
        initial_urls = [(category.split('-')[0], f"{base_url}{category}") for category in category_list]

        logging.info(f"Intial urls: {initial_urls}")

        #category_names = [category.split('-')[0] for category in category_list]


        all_urls = []
        for category, url in initial_urls:
            all_urls.extend([(category, u) for u in self.predicting_url(url)])

        logging.info(f"Here is the resulting all urls list : {all_urls}")

        return all_urls
    
    
    #Returns user agent
    def get_user_agents(self) -> List[str]:
        with open('useragents.txt') as f:
            USER_AGENT_PARTS = f.readlines()
        return USER_AGENT_PARTS

    def __init__(self, *args, **kwargs):
        super(AproxSpiderSpider, self).__init__(*args, **kwargs)
        self.start_urls = self.start_url_generator()
        self.user_agents = self.get_user_agents()
        self.blue_product_limit = 25  # Define the limit for blue products
        self.blue_products_count = {}  # Dictionary to track blue products count per URL

    #returns a random user agent
    def get_random_user_agent(self) -> str:
        return random.choice(self.user_agents)
    
    def start_requests(self):
        for category, url in self.start_urls:
            if url not in self.blue_products_count:
                self.blue_products_count[url] = 0  # Initialize blue products count for the URL
            yield scrapy.Request(url, 
                                headers={'User-Agent': self.get_random_user_agent()}, 
                                meta={'category': category},
                                callback=self.parse)
    
    def parse(self, response):
        category = response.meta.get('category')  # Retrieve category from meta
        all_products = response.css("div.name a ::text").getall()
        all_prices = response.css("div.price::text").getall()
        comparison_links = response.css("a.button-orange::attr(href)").getall()
        url = response.meta.get('url')  # Retrieve the URL from meta

        for n, p, link in zip(all_products, all_prices, comparison_links):
            if n and p and link:
                item = {
                    'name': n,
                    'price': p.strip(),
                    'url': link,
                    'category': category  # Add category to the item
                }
                yield item
            else:
                logging.error(f" -------- DATA NOT SAVED BLUE PRODUCTS :  {self.blue_products_count[url]}")
                self.blue_products_count[url] += 1
                if self.blue_products_count[url] >= self.blue_product_limit:
                    logging.info(f"Reached the limit of {self.blue_product_limit} blue products for {url}.")
                    return  # Stop making further requests for this URL


