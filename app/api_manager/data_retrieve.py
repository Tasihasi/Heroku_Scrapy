import os
import logging
from .api_proxy import wait_for_file, delete_existing_file, run_spider



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
    command = ['scrapy', 'crawl', 'arukereso_all'] #, '-O', 'Result.xml']

    logging.info("Running spider")

    # Step 2: Run the spider
    if not run_spider(command):
        return


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
    command = ['scrapy', 'crawl', 'free_proxy_list'] #, '-O', 'Result.xml']

    logging.info("Running spider")

    # Step 2: Run the spider
    if not run_spider(command):
        return

#get_data_from_scrapy()