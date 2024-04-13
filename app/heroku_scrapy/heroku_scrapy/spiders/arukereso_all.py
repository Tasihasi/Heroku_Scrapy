import scrapy
import re
import threading
import requests
import subprocess
import queue
from scrapy.selector import Selector
#from scrapy_playwright.page import PageCoroutine
import json
from scrapy.http import FormRequest
import csv
import time
import os
from scrapy import signals
from scrapy.signalmanager import dispatcher
import random
import concurrent.futures
from scrapy.crawler import CrawlerProcess
from twisted.internet import reactor, threads
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from typing import List
from urllib.parse import urlparse, urlencode, urlunparse,quote, parse_qs
import xml.etree.ElementTree as ET



import logging
#from ..proxy_manager.proxy_verification import Get_valid_Proxy_list


#logging.info("Spider started")






def Getting_new_proxies():  # Runnin the scrapy 
        # Define the command as a list of strings
        logging.info("--------------------   Getting new proxies ---------------------------")
        current_directory = os.getcwd()
        #print("Current Working Directory:", current_directory)

        url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all"
        output_file = "proxyes.txt"

        try:
            response = requests.get(url)
            retList = []

            if response.status_code == 200:
                # Successful response
                proxies = response.text
                
                # Write proxies to proxies.txt file
                with open(output_file, "w") as file:
                    file.write(proxies)
                    
                #print("Proxies retrieved and saved to proxies.txt")
                for item in proxies.split("\n"):
                    retList.append(str("http://") + item)
                    retList.append(str("https://") + item)

                #return retList

                return proxies
            else:
                # Handle other status codes if needed
                pass
                #print(f"Request failed with status code: {response.status_code}")

        except requests.RequestException as e:
            # Handle exceptions or errors
            pass
            #print(f"An error occurred: {e}")





class ArukeresoSpider(scrapy.Spider):
    name = 'arukereso_all'
    start_urls = ['https://www.arukereso.hu/nyomtato-patron-toner-c3138/']

    custom_settings = {
        'DOWNLOAD_DELAY': 0.2,  # add download delay of 1 second
        'CONCURRENT_REQUESTS': 13,  # Adjust the concurrency level as needed
        'CONCURRENT_REQUESTS_PER_DOMAIN' : 3, # for the current limit this must be so high
        'RETRY_TIMES': 5,  # Number of times to retry a failed request
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 443],  # HTTP status codes to retry

    }
    def predicting_url(self, url : str) -> List[str]:

        ret_list = [url]

        for i in range(1, 3250):
            ret_list.append(url + "?start=" + str(i*25))
        
        return ret_list
    
    def write_item_to_xml(self, item):
        filename = 'temp_output.xml'

        if os.path.exists(filename):
            tree = ET.parse(filename)
            root = tree.getroot()
        else:
            root = ET.Element('items')
            tree = ET.ElementTree(root)

        item_element = ET.Element('item')

        for key, value in item.items():
            field = ET.Element(key)
            field.text = str(value)
            item_element.append(field)

        root.append(item_element)

        with open(filename, 'wb') as file:
            tree.write(file)

    

    def __init__(self, *args, **kwargs):
        super(ArukeresoSpider, self).__init__(*args, **kwargs)
        self.blue_product = 0
        #self.valid_proxies = Get_valid_Proxy_list() #["195.123.8.186:8080"] #
        self.raw_proxy_list = Getting_new_proxies()
        self.proxies_retries = 0
        self.start_urls = self.predicting_url(self.start_urls[0])
        self.error_urls = []  # List to store URLs that encountered errors
        self.visited_url = set()

        #logging.info("----------- Got valid Proxies. ------------------")


    
    

    def select_proxy(self):
        if not self.raw_proxy_list:
            return None   

        selected_proxy = random.choice(self.raw_proxy_list)

        while selected_proxy == "-" or not selected_proxy:
            selected_proxy = random.choice(self.raw_proxy_list)

        

        return selected_proxy

    def check_proxy_status(self, proxy):
        try:
            response = requests.get("https://www.arukereso.hu/nyomtato-patron-toner-c3138/", proxies={"http": proxy, "https": proxy}, timeout=10)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        return False
        

    def parse(self, response):

        # Get a proxy for this request
        proxy = self.select_proxy()

        #logging.info(f" ---- current proxy : {proxy}")
    
        while not proxy and len(self.raw_proxy_list) <30:
            self.raw_proxy_list = Getting_new_proxies()
            self.proxies_retries+=1

            #logging.info("trying to get new  proxy list: " , self.proxies_retries)
        
        if not proxy:
            #logging.info("------------------  There was no proxies ---------   logging")
            return

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36'}


        if response.url not in self.visited_url:
            request = scrapy.Request(
                url=(response.url),
                callback=self.parse_link,
                dont_filter=True,
                meta={'proxy': str("https://")+self.select_proxy()},
                headers=headers,
            )


            #logging.info(f"Outgoing request headers: {request.headers}")
            yield request
            

        all_products = response.css("div.name a ::text").getall()
        all_prices = response.css("div.price::text").getall()
        

        # regex pattern to extract the competitor's name from the URL
        pattern = r'arukereso\.hu|.hu'
        all_competitors = response.css("a.offer-num::attr(href)").re(pattern)
        competitor = all_competitors[0] if all_competitors else ''

        comparison_links = response.css("a.button-orange::attr(href)").getall()
        
        for n, p, c, link in zip(all_products, all_prices, all_competitors, comparison_links):
            
            if n and p and c:
                if "arukereso.hu" in link and link not in self.visited_url:
                    yield scrapy.Request(url=link, callback=self.parse_link)
                else:
                    yield {'name': n, 'price': p.strip(), 'competitor': c, 'url': response.url}

                    item_data = {'name': n, 'price': p.strip(), 'competitor': c, 'url': response.url}
                    self.write_item_to_xml(item_data)

                # here is should implement the write to temporary file 

        self.visited_url.add(response.url)


            

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

            logging.info(f"The saved data {price} ,  {product_name} ,  {competitor}")

            data_tuple = tuple(data.items())
            if data_tuple not in data_list:
                data_list.add(data_tuple)
                yield data

        if response.status != 200:
            self.error_urls.append(response.url)

    def restart_parsing(self):
        # Function to replicate initial parsing behavior
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)


    # closing ----------------

    def closed(self, reason):
        if self.error_urls:
            self.start_urls = self.error_urls
            yield from self.restart_parsing()

        logging.info(f"data :  {self.data}")