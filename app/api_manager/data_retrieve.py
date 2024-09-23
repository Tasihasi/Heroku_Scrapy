import subprocess, logging, os

def run_spider(command : str) -> bool:
    try:
        # Redirecting subprocess output to stdout explicitly
        result = subprocess.run(command, stdout=subprocess.PIPE, text=True, check=True)
        
         # Capture the spider's log output
        spider_log = result.stdout
        print("Spider Log:")
        logging.info("--------  Spider log : ")
        logging.info(spider_log)
        print(spider_log)

        print("Spider Run in the api_proxy.py")
        return True, spider_log
    except subprocess.CalledProcessError as e:
        print("Failed to run the spider:", e)
        return False, None


logging.basicConfig(level=logging.DEBUG)
def get_data_from_scrapy():
    # Get the current directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Set the relative path to the Scrapy spider directory
    spider_dir = os.path.join(script_dir, '..', 'heroku_scrapy')
    print(f"Script Directory: {script_dir}")

    logging.info(f"Script Directory: {script_dir}")

     # Change the working directory to the spider directory
    os.chdir(spider_dir)
    print(f"Changed working directory to: {os.getcwd()}")

    script_directory = os.path.dirname(os.path.abspath(__file__))

    # Define the Scrapy command
    command = ['scrapy', 'crawl', 'arukereso_all', '-O', 'Result.json']

    logging.info("Running spider  the data_retrive.py")

    # Step 2: Run the spider
    if not run_spider(command):
        logging.info("not running spider")
        return
    
    logging.info("Theoreticly spider runs")


def run_aprox_spider():
    # Get the current directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Set the relative path to the Scrapy spider directory
    spider_dir = os.path.join(script_dir, '..', 'heroku_scrapy')
    #print(f"Script Directory: {script_dir}")

    #logging.info(f"Script Directory: {script_dir}")

     # Change the working directory to the spider directory
    os.chdir(spider_dir)
    print(f"Changed working directory to: {os.getcwd()}")

    script_directory = os.path.dirname(os.path.abspath(__file__))

    # Define the Scrapy command
    command = ['scrapy', 'crawl', 'aprox-spider', '-O', 'outputUrl.json']

    logging.info("Running spider  the data_retrive.py")

    # Step 2: Run the spider
    if not run_spider(command):
        logging.info("not running spider")
        return
    
    logging.info("Theoreticly spider runs")


def run_url_spider(urls):
    # Get the current directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Set the relative path to the Scrapy spider directory
    spider_dir = os.path.join(script_dir, '..', 'heroku_scrapy')
    #print(f"Script Directory: {script_dir}")

    #logging.info(f"Script Directory: {script_dir}")

     # Change the working directory to the spider directory
    os.chdir(spider_dir)
    print(f"Changed working directory to: {os.getcwd()}")

    # Join the URLs into a comma-separated string
    urls_arg = ','.join(urls)

    script_directory = os.path.dirname(os.path.abspath(__file__))

    # Define the Scrapy command
    command = ['scrapy', 'crawl', 'url-crawl', '-a', f'start_urls={urls_arg}', '-O', 'marketPrices.json']

    logging.info("Running spider  the data_retrive.py")

    # Step 2: Run the spider
    if not run_spider(command):
        logging.info("not running spider")
        return
    
    logging.info("Theoreticly spider runs")

class SpiderRunner:
    def __init__(self, spider_name, output_file, urls=None, category = None):
        self.spider_name = spider_name
        self.output_file = output_file
        self.urls = urls
        self.category = category

    def run_spider(self, command):
        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, text=True, check=True)
            spider_log = result.stdout
            print("Spider Log:")
            logging.info("--------  Spider log : ")
            logging.info(spider_log)
            print(spider_log)
            print("Spider Run in the api_proxy.py")
            return True, spider_log
        except subprocess.CalledProcessError as e:
            print("Failed to run the spider:", e)
            return False, None

    def run(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        spider_dir = os.path.join(script_dir, '..', 'heroku_scrapy')
        os.chdir(spider_dir)
        print(f"Changed working directory to: {os.getcwd()}")

        if self.urls:
            urls_arg = ','.join(self.urls)
            command = ['scrapy', 'crawl', self.spider_name, '-a', f'start_urls={urls_arg}', '-O', self.output_file]
        
        elif self.category:
            category_arg = ','.join(self.urls)
            command = ['scrapy', 'crawl', self.spider_name, '-a', f'category={category_arg}', '-O', self.output_file]

        else:
            command = ['scrapy', 'crawl', self.spider_name, '-O', self.output_file]

        logging.info(f"Running spider {self.spider_name} with output {self.output_file}")
        if not self.run_spider(command):
            logging.info("Spider did not run successfully")
            return
        logging.info("Theoretically, the spider runs")



if __name__ == '__main__':
    pass