import scrapy
from scrapy.exceptions import CloseSpider
from datetime import datetime
import requests
import time
import os
import random
from typing import List
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
import socket


import logging
#from ..proxy_manager.proxy_verification import Get_valid_Proxy_list


#logging.info("Spider started")

import socket

#Returns user agent
def get_user_agents() -> List[str]:
    with open('lists/useragents.txt') as f:
        USER_AGENT_PARTS = f.readlines()
    return USER_AGENT_PARTS


def is_port_open(host: str, port: int) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)  # One second timeout
    try:
        sock.connect((host, port))
        sock.close()
        return True
    except socket.error:
        return False
    

def port_scan(host: str, start_port: int, end_port: int) -> List[int]:
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(is_port_open, host, port): port for port in range(start_port, end_port + 1)}
        open_ports = [future.result() for future in futures if future.result() is not None]
    return open_ports



def check_proxy_status(proxy : str ) -> int:
    """
    Check if a proxy is working by making a request to a test URL.
    """
    test_url = "https://www.arukereso.hu/nyomtato-patron-toner-c3138/"

    try:
        if requests.get(proxy, timeout=5).status_code != 200:

            # TODO implement port scan
            # TODO REplace the port with the working port

            logging.info(f"Proxy {proxy} is not working")
            logging.info(f"Checking the port of the proxy {proxy.split(':')[0] }   {proxy.split(':')[1]}")
            return -1


        response = requests.get(test_url, proxies={"http": proxy, "https": proxy}, timeout=3)
        if response.status_code == 200:
            logging.info(f"Proxy {proxy} is working")
            return int(proxy.split(":")[-1])
        
        
        return -1

    except requests.RequestException:
        return False

def check_proxy_multi_threadedly(proxies : List[str] ) -> List[str]:
    """
    Check if a proxy is working by making a request to a test URL.
    """

    def check_and_format_proxy(proxy):
        if -1 < check_proxy_status(proxy):
            return proxy
        return None
    

    valid_proxies = List[str]

    with ThreadPoolExecutor(max_workers=200) as executor:
        results = executor.map(check_and_format_proxy, proxies)

    # Filter out None values and return the list of valid proxies
    valid_proxies = [proxy for proxy in results if proxy is not None]

    return valid_proxies


def Getting_new_proxies():  # Running the scrapy 



        # Define the command as a list of strings
        logging.info("--------------------   Getting new proxies ---------------------------")
        current_directory = os.getcwd()
        #print("Current Working Directory:", current_directory)

        url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=no&anonymity=elite"

        try:
            response = requests.get(url)

            if response.status_code == 200:
                # Successful response
                proxies = response.text.strip().split("\n")
                proxies = [f"http://{proxy.strip()}" for proxy in proxies]
                #proxies += [f"https://{proxy.strip()}" for proxy in proxies]
                #return retList
                logging.info(f"Proxies retrieved and saved to {proxies}")


                return check_proxy_multi_threadedly(proxies)
            else:
                # Handle other status codes if needed
                pass
                #print(f"Request failed with status code: {response.status_code}")

        except requests.RequestException as e:
            # Handle exceptions or errors
            pass
            #print(f"An error occurred: {e}")

"""
def Getting_new_proxies():  # owerwrite Running the scrapy
    url = ["https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt"]

    try:
        response = requests.get(url)

        if response.status_code == 200:
            # Successful response

            logging.info(f"Proxies retrieved and saved to {response.text.strip()}")


            proxies = response.text.strip().split("\n")
             #proxies = [f"http://{proxy.strip()}" for proxy in proxies]
            #proxies += [f"https://{proxy.strip()}" for proxy in proxies]
            #return retList
            logging.info(f"Proxies retrieved and saved to {proxies}")


            return check_proxy_multi_threadedly(proxies)
        else:
            # Handle other status codes if needed
            pass
            #print(f"Request failed with status code: {response.status_code}")

    except requests.RequestException as e:
        # Handle exceptions or errors
        pass
        #print(f"An error occurred: {e}")
"""

class ArukeresoSpider(scrapy.Spider):
    name = 'arukereso_all'
    start_urls = ['https://www.arukereso.hu/nyomtato-patron-toner-c3138/']

    custom_settings = {
        'DOWNLOAD_DELAY': 0.01,  # add download delay of 1 second
        'CONCURRENT_REQUESTS': 1, # 128,  # Adjust the concurrency level as needed
        'CONCURRENT_REQUESTS_PER_DOMAIN' : 1, # for the current limit this must be so high
        'RETRY_TIMES': 0,  # Number of times to retry a failed request
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 443],  # HTTP status codes to retry
        #   ------ closing spider aftre 50 items -------
        'CLOSESPIDER_ITEMCOUNT': 3000,
    }
    def predicting_url(self, url : str) -> List[str]:

        ret_list = [url]

        for i in range(1, 3250):
            ret_list.append(url + "?start=" + str(i*25))
        
        return ret_list
    
      

    

    def __init__(self, *args, **kwargs):
        super(ArukeresoSpider, self).__init__(*args, **kwargs)
        self.time_passing = {}
        self.request_waiting = 0
        self.crawling_time = datetime.now()
        self.proxy_time = 0
        self.parsing_time = [0,0]
        self.product_count = 0
        #self.valid_proxies = Get_valid_Proxy_list() #["195.123.8.186:8080"] #
        self.raw_proxy_list = Getting_new_proxies()
        self.valid_proxies = [proxy for proxy in self.raw_proxy_list if proxy and proxy != "-"]
        self.proxies_retries = 0
        self.start_urls = self.predicting_url(self.start_urls[0])
        self.error_urls = []  # List to store URLs that encountered errors
        self.visited_url = set()
        self.user_agents = get_user_agents()

        #logging.info("----------- Got valid Proxies. ------------------")

    #returns a random user agent
    def get_random_user_agent(self) -> str:
        return random.choice(self.user_agents)

    def select_proxy(self) -> str:
        time = datetime.now()
        if not self.raw_proxy_list:
            logging.error(f"No proxies available time took :  { datetime.now() - time}")
            return None

        # Filter out invalid proxies
        

        if not self.valid_proxies:
            return None  # Return None if no valid proxies are available

        selected_proxy = random.choice(self.valid_proxies)


        logging.warning(f" -----    !!!! Time took to get a new poxy  time took :  { datetime.now() - time}   !!!!!  ----")
        self.proxy_time += (datetime.now() - time).total_seconds()
        return selected_proxy

    def check_proxy_status(self, proxy : str)-> bool:
        time = datetime.now()
        try:
            response = requests.get("https://www.arukereso.hu/nyomtato-patron-toner-c3138/", proxies={"http": proxy, "https": proxy}, timeout=10)
            if response.status_code == 200:
                logging.info(f'-------------------  Proxy {proxy} is being used for the request.------------------------------')
                self.proxy_time += (datetime.now() - time).total_seconds()
                return True
        except requests.exceptions.RequestException:
            logging.info(f'------------------------- Proxy {proxy} is not being used for the request.--------------------')
            pass
        self.proxy_time += (datetime.now() - time).total_seconds()
        return False

    def remove_proxy(self, proxy : str) -> None:
        if proxy in self.valid_proxies:
            self.valid_proxies.remove(proxy)

        return 
            #raise CloseSpider("closed the spider manually at line 176")

            # this function will remove the proxy from the list
            #self.raw_proxy_list.remove(failure.request.meta['proxy'])
        
    def start_requests(self):
        logging.info("--------------   !!!!!   Spider started !!!!!!!!  ------------------")

        # Get a proxy for this request
        proxy = self.select_proxy()

        proxy_time = datetime.now()
        while not proxy and len(self.raw_proxy_list) <30:

            self.raw_proxy_list = Getting_new_proxies()
            self.proxies_retries+=1

            logging.info("trying to get new  proxy list: " , self.proxies_retries)
        
        self.proxy_time += (datetime.now() - proxy_time).total_seconds()



        
        with ThreadPoolExecutor(max_workers=4) as executor:
            for url in self.start_urls:
                yield scrapy.Request(url, meta={'proxy': self.select_proxy()}, header={'User-Agent': self.get_random_user_agent()})

        logging.info(f" ---- SPidre started IN THE START REQUESTS ----  {datetime.now() - self.crawling_time}  ----")

    def parse(self, response):
        start_time = datetime.now()
        if "start parsing start" not in self.time_passing:
            self.time_passing["start parsing start"] = []

        self.time_passing["start parsing start"].append((datetime.now() - self.crawling_time).total_seconds())
        # Get a proxy for this request
        proxy = self.select_proxy()

        proxy_time = datetime.now()
        while not proxy and len(self.raw_proxy_list) <30:

            self.raw_proxy_list = Getting_new_proxies()
            self.proxies_retries+=1

            logging.info("trying to get new  proxy list: " , self.proxies_retries)
        
        self.proxy_time += (datetime.now() - proxy_time).total_seconds()

        logging.info(f" ---- current proxy : {proxy}")

       

        if not proxy:
            #logging.info("------------------  There was no proxies ---------   logging")
            return

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36'}


        
        request_wait = datetime.now()
        if response.url not in self.visited_url:
            request = scrapy.Request(
                url=(response.url),
                callback=self.parse_link,
                dont_filter=True,
                errback=self.remove_proxy(proxy),  # add this line
                meta={'proxy': str("https://")+self.select_proxy()},
                headers=self.get_random_user_agent(),
            )


            #logging.info(f"Outgoing request headers: {request.headers}")
            yield request

        self.request_waiting += (datetime.now() - request_wait).total_seconds()  

        all_products = response.css("div.name a ::text").getall()
        all_prices = response.css("div.price::text").getall()
        

        # regex pattern to extract the competitor's name from the URL
        pattern = r'arukereso\.hu|.hu'
        all_competitors = response.css("a.offer-num::attr(href)").re(pattern)
        competitor = all_competitors[0] if all_competitors else ''

        comparison_links = response.css("a.button-orange::attr(href)").getall()
        parse_links = []

        for n, p, c, link in zip(all_products, all_prices, all_competitors, comparison_links):
            
            if n and p and c:
                if "arukereso.hu" in link and link not in self.visited_url:
                    parse_links.append(link)
                    #yield scrapy.Request(url=link, callback=self.parse_link)
                else:
                    yield {'name': n, 'price': p.strip(), 'competitor': c, 'url': response.url}

                    item_data = {'name': n, 'price': p.strip(), 'competitor': c, 'url': response.url}
                    self.write_item_to_xml(item_data)

                # here is should implement the write to temporary file 

        with ThreadPoolExecutor(max_workers=25) as executor:
            for link in parse_links:
                yield scrapy.Request(url=link, callback=self.parse_link, meta={'proxy': self.select_proxy()}, headers=headers)
        
        self.visited_url.add(response.url)
        logging.critical(f" --------   Time taken for the request in Parse: {datetime.now() - start_time}   -------")
        self.parsing_time[0] += (datetime.now() - start_time).total_seconds()
        if "end parsing" not in self.time_passing:
            self.time_passing["end parsing"] = []

        self.time_passing["end parsing"].append((datetime.now() - self.crawling_time).total_seconds())

    def parse_link(self, response):
        start_time = datetime.now()
        if "start parsing link" not in self.time_passing:
            self.time_passing["start parsing link"] = []

        self.time_passing["start parsing link"].append((datetime.now() - self.crawling_time).total_seconds())

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

        if response.status != 200:
            self.error_urls.append(response.url)

        self.product_count += 1
        logging.critical(f" --------   Time taken for the request in Parse  _ link: {datetime.now() - start_time}   -------")
        self.parsing_time[1] += (datetime.now() - start_time).total_seconds()
        if "end parsing link" not in self.time_passing:
            self.time_passing["end parsing link"] = []

        self.time_passing["end parsing link"].append((datetime.now() - self.crawling_time).total_seconds())

    def restart_parsing(self):
        return
        # Function to replicate initial parsing behavior
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    # ----------------- Pushing to google drive ---------------------

    def push_to_google_drive(self, path : str):
        shrek_key =  os.getenv('shrek_api_key')
        home_url = os.getenv("home_url")


        # Define the file name and MIME type
        current_date = datetime.now().strftime('%Y-%m-%d')  # Get the current date as a string
        file_name = f"{current_date}.csv"  # Set the file name to the current date
        file_mimeType = "csv"  # Replace with your actual MIME type

        # Get the current directory
        current_directory = os.getcwd()

        # Get the list of all files and directories in the current directory
        directory_content = os.listdir(current_directory)

        # Print the content of the current directory
        for item in directory_content:
            logging.info(f"Here is a file :  {item}")


        # Open the file in read mode ('r')
        with open(path, 'r') as file:
            # Read the content of the file
            content = file.read()

        # Print the content of the file
        logging.info(f"Here is the content :  {content}")

        
        # Define the API endpoint URL
        endpoint_url = f"{home_url}/create_file/{file_name}/{file_mimeType}/1"
        

        logging.info(f"Here is the url that for what the http request is being sent:   {endpoint_url}")
        try:
            headers = {"shrek_key": shrek_key}


            response = requests.post(endpoint_url, headers=headers, data=content)

            logging.info(f"Response from the server: {response.text}")

        except Exception as e:
            logging.info("Error in pushing to google drive")
            logging.error("An error occurred:", e)



    # closing ----------------

    def closed(self, reason):
        #if self.error_urls:
            #self.start_urls = self.error_urls
            #yield from self.restart_parsing()
        
        logging.critical(f"  ------  Time took to manage proxies : {self.proxy_time}  ------")
        logging.critical(f" -------  Time took parsing the data : {self.parsing_time[0]}  -------")
        logging.critical(f" -------  Time took parsing the link : {self.parsing_time[1]}  -------")
        logging.critical(f" -------  Time took parsing SUM : {sum(self.parsing_time)}  -------")
        logging.critical(f" -------  Time took run the spider : {(datetime.now() - self.crawling_time).total_seconds()}  -------")
        logging.critical(f" -------  Times getting new proxies  : {self.proxies_retries}  -------")
        logging.critical(f" -------  Times waiting for the request : {self.time_passing}  -------")

        #self.push_to_google_drive("output.jsonl")
        


    
