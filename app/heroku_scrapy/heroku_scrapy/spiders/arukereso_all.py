from datetime import datetime
import random, logging, socket, os, gzip, requests, scrapy, time
from typing import List
from concurrent.futures import ThreadPoolExecutor
from ..proxy_manager import ProxyHandler


class ArukeresoSpider(scrapy.Spider):
    name = 'arukereso_all'
    start_urls = ['https://www.arukereso.hu/nyomtato-patron-toner-c3138/']

    custom_settings = {
        'DOWNLOAD_DELAY': 0.01,  # add download delay of 1 second
        'CONCURRENT_REQUESTS': 1, # 128,  # Adjust the concurrency level as needed
        'CONCURRENT_REQUESTS_PER_DOMAIN' : 2_000, # for the current limit this must be so high
        'RETRY_TIMES': 0,  # Number of times to retry a failed request
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 443],  # HTTP status codes to retry
        #   ------ closing spider aftre 50 items -------
        #'CLOSESPIDER_ITEMCOUNT': 10,
    }

    # Creates a list of urls from the simple url 
    def predicting_url(self, url : str) -> List[str]:
        ret_list = [url]
        for i in range(1, 3250):
            ret_list.append(url + "?start=" + str(i*25))
        
        return ret_list

    def __init__(self, *args, **kwargs):
        logging.info(f"current directore : {os.getcwd()}")
        logging.info(f"Current files in the directory : {os.listdir()}")
        super(ArukeresoSpider, self).__init__(*args, **kwargs)
        self.time_passing = {}
        self.request_waiting = 0
        self.crawling_time = datetime.now()
        self.proxy_time = 0
        self.parsing_time = [0,0]
        self.product_count = 0
        #self.valid_proxies = Get_valid_Proxy_list() #["195.123.8.186:8080"] #
        self.raw_proxy_list = [] #Getting_new_proxies()
        self.valid_proxies = [] #[proxy for proxy in self.raw_proxy_list if proxy and proxy != "-"]
        self.proxies_retries = 0
        self.start_urls = self.predicting_url(self.start_urls[0])
        self.error_urls = []  # List to store URLs that encountered errors
        self.visited_url = set()
        self.Proxy_handler = ProxyHandler()
   
    def start_requests(self):

        logging.info("------------------ python started -----------------------")

        proxy = self.Proxy_handler.get_proxy()
        proxy_time = datetime.now()
        
        with ThreadPoolExecutor(max_workers=200) as executor:
            for url in self.start_urls:
                yield scrapy.Request(url,  headers={'User-Agent': self.Proxy_handler.get_random_user_agent()}) #meta={'proxy': self.select_proxy()},

    def parse(self, response):
        start_time = datetime.now()
        if "start parsing start" not in self.time_passing:
            self.time_passing["start parsing start"] = []

        self.time_passing["start parsing start"].append((datetime.now() - self.crawling_time).total_seconds())

        headers = {'User-Agent': self.Proxy_handler.get_random_user_agent()}

        all_products = response.css("div.name a ::text").getall()
        all_prices = response.css("div.price::text").getall()
        

        # regex pattern to extract the competitor's name from the URL
        pattern = r'arukereso\.hu|.hu'
        all_competitors = response.css("a.offer-num::attr(href)").re(pattern)
        competitor = all_competitors[0] if all_competitors else ''

        comparison_links = response.css("a.button-orange::attr(href)").getall()
        parse_links = []

        for n, p, c, link in zip(all_products, all_prices, all_competitors, comparison_links):
            
            if n and p and c and link:
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
                headers = {'User-Agent': self.Proxy_handler.get_random_user_agent()}
                yield scrapy.Request(url=link, callback=self.parse_link,
                                      #meta={'proxy': self.select_proxy()},
                                        headers=headers)
        
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

  
    # ----------------- Pushing to google drive ---------------------

    def push_to_google_drive(self, path : str):
        shrek_key =  os.getenv('shrek_api_key')
        home_url = os.getenv("home_url")


        # Define the file name and MIME type
        current_date = datetime.now().strftime('%Y-%m-%d')  # Get the current date as a string
        file_name = f"{current_date}_printer"  # Set the file name to the current date
        file_mimeType = "gzip"  # Replace with your actual MIME type

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

        # Compress the content
        compressed_content = gzip.compress(content.encode())

        
        # Define the API endpoint URL
        endpoint_url = f"{home_url}/create_file/{file_name}/{file_mimeType}/1"
        

        logging.info(f"Here is the url that for what the http request is being sent:   {endpoint_url}")
        try:
            headers = {"shrek_key": shrek_key}


            response = requests.post(endpoint_url, headers=headers, data=compressed_content)

            logging.info(f"Response from the server: {response.text}")

        except Exception as e:
            logging.info("Error in pushing to google drive")
            logging.error("An error occurred:", e)



    # closing ----------------
    def closed(self, reason):
        return
        self.push_to_google_drive("output.jsonl")
        


    
