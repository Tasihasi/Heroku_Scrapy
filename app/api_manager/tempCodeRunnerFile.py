import subprocess
import os
import time

def wait_for_file(file_path, timeout=120, polling_interval=1):
    start_time = time.time()
    while not os.path.exists(file_path):
        if time.time() - start_time > timeout:
            raise TimeoutError(f"Timed out waiting for {file_path} to become available.")
        time.sleep(polling_interval)
        print("Checking for 'scraping_completed.signal'...")
    print("File is found.!!!!! ------------------")

def gather_proxy_data():
    # Get the current directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Script Directory: {script_dir}")
    
    # Set the relative path to the Scrapy spider directory
    spider_dir = os.path.join(script_dir, '..', 'scrapy', 'proxy_manager', 'proxy_scraper')
    print(f"Spider Directory: {spider_dir}")

    # Change the working directory to the spider directory
    os.chdir(spider_dir)
    print(f"Changed working directory to: {os.getcwd()}")

    # Define the relative path to the JSON file
    json_file_path = os.path.join(script_dir, 'proxy_ips.json')
    print(f"JSON File Path: {json_file_path}")

    # Remove the existing JSON file if it exists
    if os.path.exists(json_file_path):
        os.remove(json_file_path)
        print("Deleted existing JSON file")

    # Define the Scrapy command
    command = ['scrapy', 'crawl', 'proxynova', '-O', 'proxy_ips.json']

    # Define the path to the "scraping_completed.signal" file
    signal_file_path = os.path.join(spider_dir, 'scraping_completed.signal')

    # Wait for the "scraping_completed.signal" file to become available
    wait_for_file(signal_file_path, timeout=120, polling_interval=1)

    # If the "scraping_completed.signal" file is available, the scraping is complete
    print("Scraping is complete. Proceed with further processing.")

    try:
        # Execute the Scrapy command and capture the output
        result = subprocess.run(command, capture_output=True, text=True, check=True)

        # Print the result for debugging
        print("STDOUT:")
        print(result.stdout)
        print("STDERR:")
        print(result.stderr)

        # Wait for the JSON file to become available
        wait_for_file(json_file_path, timeout=120, polling_interval=1)

        # Check if the command was successful and the JSON file was created
        if result.returncode == 0 and os.path.exists(json_file_path):
            with open(json_file_path, 'r') as json_file:
                data = json_file.read()
                print("JSON Content:")
                print(data)  # Print the JSON content
                return data  # Return the JSON data
        else:
            print("Scrapy spider execution failed")
            return {"message": "Scrapy spider execution failed"}
    except subprocess.CalledProcessError as e:
        print("big fail")
        return {"message": f"Error: {e}"}

    

gather_proxy_data()
