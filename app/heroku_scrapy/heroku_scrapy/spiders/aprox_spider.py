import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from typing import List
import logging
import random
import os
from concurrent.futures import ThreadPoolExecutor
import requests






class AproxSpiderSpider(CrawlSpider):
    name = "aprox-spider"
    rules = (Rule(LinkExtractor(allow=r"Items/"), callback="parse_item", follow=True),)


    custom_settings = {
        'DOWNLOAD_DELAY': 0.01,  # add download delay of 1 second
        'CONCURRENT_REQUESTS': 1, # 128,  # Adjust the concurrency level as needed
        'CONCURRENT_REQUESTS_PER_DOMAIN' : 1_000, # for the current limit this must be so high
        'RETRY_TIMES': 0,  # Number of times to retry a failed request
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 443],  # HTTP status codes to retry
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

    # Generate the start URLs that the spider cralws
    def start_url_generator(self) -> list[str]:
        # Assing the sub categories to crawl
        category_list = ["nyomtato-patron-toner-c3138/",
                         "szamitogep-periferia-c3107/"]

        base_url = ["https://www.arukereso.hu/"]

        # Generate the base URLs for each category
        initial_urls = [f"{base_url}{category}" for category in category_list]

        # Apply predicting_url to each URL to account for pagination
        all_urls = []
        for url in initial_urls:
            all_urls.extend(self.predicting_url(url))

        return all_urls
    
    #Returns user agent
    def get_user_agents(self) -> List[str]:
        with open('useragents.txt') as f:
            USER_AGENT_PARTS = f.readlines()
        return USER_AGENT_PARTS

    def __init__(self):
        self.start_urls = self.start_url_generator()
        self.user_agents = self.get_user_agents()









    def parse_item(self, response):
        item = {}
        #item["domain_id"] = response.xpath('//input[@id="sid"]/@value').get()
        #item["name"] = response.xpath('//div[@id="name"]').get()
        #item["description"] = response.xpath('//div[@id="description"]').get()
        return item

    #returns a random user agent
    def get_random_user_agent(self) -> str:
        return random.choice(self.user_agents)
    
    def start_requests(self):
        with ThreadPoolExecutor(max_workers=100) as executor:
            for url in self.start_urls:
                yield scrapy.Request(url,  headers={'User-Agent': self.get_random_user_agent()}) #meta={'proxy': self.select_proxy()},

    def parse(self, response):
        #Extracting the names, prices and links from the response
        all_products = response.css("div.name a ::text").getall()
        all_prices = response.css("div.price::text").getall()
        comparison_links = response.css("a.button-orange::attr(href)").getall()

        for n, p, link in zip(all_products, all_prices, comparison_links):
            
            if n and p and link:
                    yield {'name': n, 'price': p.strip(),  'url': response.url}

        
     

