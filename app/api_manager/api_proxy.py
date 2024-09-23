import subprocess, logging
import os
import time
import json

def wait_for_file(file_path, timeout=120, polling_interval=1):
    start_time = time.time()
    while not os.path.exists(file_path):
        if time.time() - start_time > timeout:
            raise TimeoutError(f"Timed out waiting for {file_path} to become available.")
        time.sleep(polling_interval)
        print(f"Checking for {file_path}...")

def delete_existing_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
        print("Deleted existing JSON file")
        return True
    else:
        print("No existing JSON file to delete.")
        return True  # Consider this step successful even if there's no file to delete


def gather_proxy_data():
    # Get the current directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Set the relative path to the Scrapy spider directory
    spider_dir = os.path.join(script_dir, '..', 'scrapy', 'proxy_manager', 'proxy_scraper')
    print(f"Script Directory: {script_dir}")

    # Change the working directory to the spider directory
    os.chdir(spider_dir)
    print(f"Changed working directory to: {os.getcwd()}")

    script_directory = os.path.dirname(os.path.abspath(__file__))

    # Define the relative path to the JSON file
    json_file_path = os.path.join(script_directory, '..\scrapy\proxy_manager\proxy_scraper\proxy_ips.json')
    print(f"JSON File Path: {json_file_path}")

    # Step 1: Delete existing JSON file
    if not delete_existing_file(json_file_path):
        return

    # Define the Scrapy command
    command = ['scrapy', 'crawl', 'proxynova', '-O', 'proxy_ips.json']

    # Step 2: Run the spider
    if not run_spider(command):
        return

    # Step 3: Wait for the JSON file to become available
    wait_for_file(json_file_path, timeout=120, polling_interval=1)

    # Step 4: Check if the JSON file is available
    if not is_there_json(json_file_path):
        print("JSON file not found.")
        return

    # If all steps are successful, return the JSON content
    with open(json_file_path, 'r') as json_file:
        data = json.load(json_file)
        print("JSON Content:")
        print(data)  # Print the JSON content
        return data

    # If any step fails, return an error message
    print("Scrapy spider execution failed")
    return {"message": "Scrapy spider execution failed"}

def is_there_json(json_file_path):
    if os.path.exists(json_file_path):
        return True
    return False


