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


import logging
#from ..proxy_manager.proxy_verification import Get_valid_Proxy_list


logging.info("Spider started")

"""
def check_proxies(q, valid_proxy_list):
        while not q.empty():
            proxy = q.get()
            try:
                res = requests.get("https://tablet-pc.arukereso.hu/", 
                                proxies={"http": proxy, "https": proxy})
            except:
                continue
            if res.status_code == 200:
                valid_proxy_list.append(proxy)
"""

def run_scrapy_in_thread():
    runner = CrawlerRunner()

    # This function will be called in a thread
    def crawl():
        d = runner.crawl(FreeProxyListSpider)
        d.addBoth(lambda _: reactor.stop())

    # Run the crawl function in the reactor thread
    threads.deferToThread(crawl)

    # Start the reactor
    reactor.run()


def check_proxies(q, valid_proxy_list, num_threads=10):
    def check_proxy(proxy):
        logging.info("Currently checking this proxy: ", proxy)
        #print("logging in print: ", proxy)
        try:
            res = requests.get("https://tablet-pc.arukereso.hu/", 
                               proxies={"http": proxy, "https": proxy},
                               timeout=2.5 )
            
        except Exception as e:
            print("Exception occurred:", e)
            return

        logging.info("Response Code for %s: %s", proxy, res.status_code)
        #print("logging in print: ", res.status_code)
        if res.status_code == 200:
            valid_proxy_list.append(proxy)

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        # Submit proxy checking tasks to the thread pool
        while not q.empty():
            proxy = q.get()
            executor.submit(check_proxy, proxy)

def Getting_new_proxies():  # Runnin the scrapy 
        # Define the command as a list of strings
        print()
        print("--------------------   Getting new proxies ---------------------------")
        logging.info("--------------------   Getting new proxies ---------------------------")
        current_directory = os.getcwd()
        print("Current Working Directory:", current_directory)
        print()

        # Define the command as a list of strings
        command = ['scrapy', 'crawl', 'free_proxy_list', '-O', 'proxies.txt']

        # Run the command
        subprocess.run(command)



        #command = ['scrapy', 'crawl', 'free_proxy_list', '-O', 'proxies.txt']

        # Run the command
        #result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #print(result.stdout.decode())
        #print(result.stderr.decode())
        #logging.info(result.stdout.decode())
        #logging.error(result.stderr.decode())

        #subprocess.run(command)

        #run_scrapy_in_thread()

def Get_valid_Proxy_list(): # Return with a list of valid proxies or with a false value      
    logging.info("---- Get_valid_proxy_list arukereso_all.py---")
    
    q = queue.Queue()
    valid_proxy_list = []

    file_name = "./proxies.txt"

    Getting_new_proxies()
    j = 0
        
    while j < 11 and  not os.path.isfile(file_name):
        Getting_new_proxies()
        j+=1

    if os.path.isfile(file_name):
        # Open the file and read its contents
        with open(file_name, "r") as f:
                lines = f.readlines()

        # Check if there are at least 3 lines in the file
        if len(lines) >= 3:
            # Remove the first 3 lines
            del lines[:3]

            # Write the modified content back to the file
            with open(file_name, "w") as f:
                    f.writelines(lines)
        else:
            # Handle the case where there are fewer than 3 lines in the file
            print("Not enough lines to remove.")

        with open(file_name, "r") as f:
            proxies = f.read().split("\n")
            for p in proxies:
                q.put(p)

        threads = []

        for _ in range(3):
            thread = threading.Thread(target=check_proxies, args=(q, valid_proxy_list))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        # Check if you have found 15 valid proxies
        if len(valid_proxy_list) >= 15:
            return valid_proxy_list

        return valid_proxy_list
    else:
        print("There was no file here!!")
        return valid_proxy_list



class ArukeresoSpider(scrapy.Spider):
    name = 'arukereso_all'
    start_urls = ['https://www.arukereso.hu/nyomtato-patron-toner-c3138/']

    custom_settings = {
        'DOWNLOAD_DELAY': 0.2,  # add download delay of 1 second
        'CONCURRENT_REQUESTS': 10,  # Adjust the concurrency level as needed

    }

    def __init__(self, *args, **kwargs):
        super(ArukeresoSpider, self).__init__(*args, **kwargs)
        self.blue_product = 0
        #self.valid_proxies = Get_valid_Proxy_list() #["195.123.8.186:8080"] #
        self.proxies_retries = 0
        print("----------- Got valid Proxies. ------------------")
        logging.info("----------- Got valid Proxies. ------------------")
        logging.info("---  Here is the self.valid_proxy list:  ", self.valid_proxies)


        # Start a thread to periodically update the proxy list
        # it starts a new reactore and breks the code 

        # -------  Temporary closing this line ------ !!!
        #update_thread = threading.Thread(target=self.update_proxy_list)
        #update_thread.daemon = True  # This will make the thread exit when the main program exits
        #update_thread.start()

    
    def update_proxy_list(self):
        while True:
            if len(self.valid_proxies) < 10:
                new_proxies = Get_valid_Proxy_list()  # Fetch new proxies here
                self.valid_proxies.extend(new_proxies)

            # Sleep for some time before checking again
            time.sleep(60)  # Adjust the interval as needed



    def select_proxy(self):
        # Select a random proxy from the list of valid proxies
        #print("here is the self.valid proxies: ")
        #print(self.valid_proxies)

        return random.choice(self.valid_proxies)

    def check_proxy_status(self, proxy):
        try:
            response = requests.get("https://tablet-pc.arukereso.hu/", proxies={"http": proxy, "https": proxy}, timeout=10)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        return False
        

    def parse(self, response):

        # Get a proxy for this request
        #proxy = self.select_proxy()
    
        #while not proxy and self.proxies_retries <10:
            #self.valid_proxies = Get_valid_Proxy_list()
            #self.proxies_retries+=1

            #logging.info("trying to get new  proxy list: " , self.proxies_retries)
        
        #if not proxy:
            #logging.info("------------------  There was no proxies ---------   logging")
            #print("--------------- There was no proxies in the Parse Function ------------")
            #return


        request = scrapy.Request(
            url=response.url,
            callback=self.parse_link,
            dont_filter=True,
            #meta={'proxy': proxy}
        )

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
                if "arukereso.hu" in link:
                    #print(n,p,c)
                    yield scrapy.Request(url=link, callback=self.parse_link)
                else:
                    yield {'name': n, 'price': p.strip(), 'competitor': c}
                    self.blue_product += 1

        next_page = response.css('div.pagination a[data-akpage=">"]::attr(href)').get()
        if next_page:
            yield response.follow(next_page, self.parse)

        # Checking if the proxy is still alive
        if self.check_proxy_status(proxy):
            # Chossing new proxy if there are proxies
            if proxy:
                proxy = self.select_proxy()
            else:
                print("--------------- There was no proxies in the Parse Function ------------")
                return
        else:
            # Removing proxy from the list if not responding
            # Excluding the value error possibility
            if proxy in self.valid_proxies:
                self.valid_proxies.remove(proxy)
            
        
        # Check if you need to get new proxies (e.g., fewer than 10 valid proxies)
        # Temporarly removing this codition !!!!! --------N
        #if len(self.valid_proxies) < 5:
            #pass
            #self.valid_proxies = Get_valid_Proxy_list()

        logging.info("-------------------------- Reached the bottom of parse function in arukereso_all.py ----------------------")


    def parse_link(self, response):
        prices = response.css('span[itemprop="price"]::text').getall()
        availabilities = response.css('span.delivery-time::text').getall()
        competitors = response.css('div.shopname::text').getall()
        
        # concatenate the text from the nested span tags to get the product name
        product_name = ' '.join(response.css('h1.hidden-xs span::text').getall())
        
        # clean up the data
        prices = [p.replace(' ', '').replace('Ft', '') for p in prices]
        availabilities = [a.lower() for a in availabilities]

        # iterate through the extracted data and yield a dictionary for each item
        lowest_data = None
        lowest_data_price = -1


        i = 0

        for price, availability, competitor in zip(prices, availabilities, competitors):
            i+=1
            data = {
                'price': price,
                'availability': availability,
                'competitor': competitor,
                'product_name': product_name  # use the extracted product name here
            }

            if not lowest_data:
                lowest_data = data
                lowest_data_price = int(data['price'])

            elif lowest_data_price > int(data['price']):
                lowest_data = data
                lowest_data_price = int(data['price'])

            if i == 10:
                break
        
        logging.INFO("Here is the data i think: ", lowest_data)
        yield lowest_data

    def csvFile_Reader(self):
        pass

class FreeProxyListSpider(scrapy.Spider):
    name = 'free_proxy_list'
    start_urls = ['https://free-proxy-list.net/']

    def parse(self, response):
        # Check if the "Get raw list" link is present in the page source
        raw_list_link = response.css('a[title="Get raw list"][data-toggle="modal"]::attr(href)').get()

        if raw_list_link:
            # Extract the link
            raw_list_url = response.urljoin(raw_list_link)
            yield {
                'raw_list_url': raw_list_url,
            }
            
            # Now, let's extract the content of the <textarea>
            textarea_content = response.css('textarea.form-control[readonly="readonly"]::text').get()
            if textarea_content:
                # You can extract the desired content here
                yield {
                    'textarea_content': textarea_content.strip(),
                }
                
                # Save the extracted content to a text file
                self.save_to_file(textarea_content.strip())
            else:
                self.logger.warning('Textarea content not found on the page.')
        else:
            self.logger.warning('"Get raw list" link not found on the page.')

    def save_to_file(self, content):
        with open('proxies.txt', 'w') as file:
            file.write(content)


