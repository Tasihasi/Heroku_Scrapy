import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from typing import List
import random
import logging

class UrlCrawlSpider(CrawlSpider):
    name = "url-crawl"


    custom_settings = {
        'DOWNLOAD_DELAY': 0.01,  # add download delay of 1 second
        'CONCURRENT_REQUESTS': 1, # 128,  # Adjust the concurrency level as needed
        'CONCURRENT_REQUESTS_PER_DOMAIN' : 2_000, # for the current limit this must be so high
        'RETRY_TIMES': 0,  # Number of times to retry a failed request
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 443],  # HTTP status codes to retry
        'ROBOTSTXT_OBEY' : False,
        #   ------ closing spider aftre 50 items -------
        #'CLOSESPIDER_ITEMCOUNT': 100,
    }

        #Returns user agent
    def get_user_agents(self) -> List[str]:
        with open('useragents.txt') as f:
            USER_AGENT_PARTS = f.readlines()
        return USER_AGENT_PARTS
    
    def get_random_user_agent(self) -> str:
        return random.choice(self.user_agents)
  
    def __init__(self, *args, **kwargs):
        super(UrlCrawlSpider, self).__init__(*args, **kwargs)
        self.user_agents = self.get_user_agents()
        start_urls_arg = kwargs.get('start_urls', None)
        if start_urls_arg:
            self.start_urls = start_urls_arg.split(',')
        #self.start_urls = ["https://www.arukereso.hu/nyomtato-patron-toner-c3138/canon/pg-545xl-black-bs8286b001aa-p197948661/"]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, 
                                headers={'User-Agent': self.get_random_user_agent()}, 
                                callback=self.parse_link)
            
            
    
    def parse_link(self, response):
        prices = ""
        competitors = ""

        prices = response.css('span[itemprop="price"]::text').getall()
        availabilities = response.css('span.delivery-time::text').getall()
        competitors = response.css('div.shopname::text').getall()

        if len(prices) == 0 or not prices:
            prices = response.css('div.row-price > span::text').getall()

        if len(competitors) == 0 or not competitors:
            competitors = response.css('div.col-logo img::attr(alt)').getall()

        
        # concatenate the text from the nested span tags to get the product name
        product_name = ' '.join(response.css('h1.hidden-xs span::text').getall())
        
        # clean up the data
        prices = [p.replace(' ', '').replace('Ft', '') for p in prices]
        availabilities = [a.lower() for a in availabilities]

        i = 0
        data = {}
        data_list = set()

        for price, availability, competitor in zip(prices, availabilities, competitors):
            i+=1
            data = {
                'price': price,
                'availability': availability,
                'competitor': competitor,
                'product_name': product_name,  # use the extracted product name here
                'url' : response.url
            }

            #logging.info(f"The saved data {price} ,  {product_name} ,  {competitor}")

            data_tuple = tuple(data.items())
            if data_tuple not in data_list:
                data_list.add(data_tuple)
                yield data



        