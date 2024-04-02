import os
import logging
from .api_proxy import run_spider
import psutil


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


def get_link_data_from_scrapy():
    # Get the current directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Set the relative path to the Scrapy spider directory
    spider_dir = os.path.join(script_dir, '..', 'heroku_scrapy')
    logging.info(f"Script Directory: {script_dir}")

    # Change the working directory to the spider directory
    os.chdir(spider_dir)
    logging.info(f"Changed working directory to: {os.getcwd()}")

    # Terminate all other running spiders
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        # Check if the process name or command line contains 'scrapy'
        if 'scrapy' in proc.info['name'] or 'scrapy' in ' '.join(proc.info['cmdline']):
            proc.kill()
            logging.info(f"Terminated process {proc.info['pid']}")

    # Define the Scrapy command for the desired spider
    command = ['scrapy', 'crawl', 'arukereso_link', '-O', 'link_data.json']

    logging.info("Running spider to get link data...")

    # Step 2: Run the spider
    return run_spider(command)

def get_proxies():
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
    command = ['scrapy', 'crawl', 'free_proxy_list' , '-O', 'Result.xml']

    logging.info("Running spiderin the data_retrive.py")

    # Step 2: Run the spider
    if not run_spider(command):
        return

