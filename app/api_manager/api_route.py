from flask import Blueprint, jsonify, request, Response, send_file, stream_with_context
import xml.etree.ElementTree as ET
import json
import os
import logging
from .auth import is_valid_api_key
from .data_retrieve import get_data_from_scrapy, run_aprox_spider, run_url_spider, SpiderRunner
from concurrent.futures import ThreadPoolExecutor  # For async execution
import threading
from functools import partial

# TODO Use Proper HTTP Methods: 
# Ensure that each endpoint uses the appropriate HTTP method (GET, POST, PUT, DELETE) according to its purpose.
# TODO Use Proper Status Codes: 
# Return proper HTTP status codes to indicate the result of an API request (200, 201, 400, 401, 404, 500, etc.).
# TODO Resource Naming:
#  Use nouns for endpoint paths rather than verbs and keep them consistent and meaningful.
# TODO Endpoint Structure: 
# Ensure the endpoints are intuitive and hierarchical where necessary.
# TODO  Avoid Actions in URL: 
# Actions should be defined by HTTP methods, not by including verbs in the endpoint URL.


def remove_incomplete_last_item(xml_string, required_attributes):
    # Parse the XML string into an ElementTree
    root = ET.fromstring(xml_string)

    # Find the last <item> element
    last_item = root.find('.//item[last()]')

    # Check if the last <item> has all required attributes
    if last_item is not None and all(attr in last_item.attrib for attr in required_attributes):
        return xml_string  # No changes needed if the last <item> is complete

    # Remove the incomplete last <item> element
    if last_item is not None:
        root.remove(last_item)

    # Convert the modified ElementTree back to an XML string
    modified_xml_string = ET.tostring(root, encoding='utf-8').decode('utf-8')

    return modified_xml_string

# remowing the last line from the jsonl file 
# stripping all values in the jsonl file 
# returns the file name to the resulting file 
def process_jsonl(input_path, output_filename="BigOutput.jsonl", required_keys=["price", "availability", "competitor", "product_name"]):
    try:
        # Read the content from the input JSONL file
        with open(input_path, 'r', encoding="utf-8") as input_file:
            lines = [line.strip() for line in input_file.readlines()]

        # Remove the last line and strip whitespace from all values
        data = []
        for line in lines:
            try:
                record = json.loads(line)
                data.append(record)
            except json.JSONDecodeError as e:
                logging.error(f"Error decoding JSON for line: {line}. Error: {e}")

        stripped_data = [{key: value.strip() if isinstance(value, str) else value for key, value in record.items()} for record in data]

        # Filter records based on the presence of required keys
        filtered_data = [record for record in stripped_data if all(key in record for key in required_keys)]
        #logging.info(f"this is the filtered_data:  {filtered_data}" )

        # Remove the "availability" column from each record in filtered_data
        for record in filtered_data:
            if "availability" in record:
                del record["availability"]

        # trying to return with simply filtered data 
        return json.dumps(filtered_data, indent=2)

        # Write the modified content to the output JSONL file
        output_path = output_filename
        with open(output_path, 'w', encoding="utf-8") as output_file:
            for record in filtered_data:
                #logging.info(f"Current record added :   {record}")
                output_file.write(json.dumps(record) + '\n')

        #logging.info("---------------  Successfully transformed the JSONL --------")
        return output_path

    except Exception as e:
        # Handle exceptions (e.g., file not found, JSON decoding error)
        logging.error(f"------   Error processing JSONL file: {e} -----")
        return None

def strip_values_in_jsonl(jsonl_file):
    stripped_lines = []

    with open(jsonl_file, 'r', encoding="utf-8") as file:
        # Read all lines into a list, excluding the last line
        file = list(jsonl_file)[:-1]

        for line_number, line in enumerate(file, start=1):
            try:
                # Parse JSON from the line
                json_data = json.loads(line)

                # Strip whitespace from all values in the JSON object
                stripped_json_data = {key: str(value).strip() for key, value in json_data.items()}

                # Convert the modified JSON object back to a JSON-formatted string
                stripped_line = json.dumps(stripped_json_data, ensure_ascii=False)

                stripped_lines.append(stripped_line)

            except json.JSONDecodeError as e:
                # Handle JSON decoding errors if needed
                print(f"Error on line {line_number}: {e}")

    return stripped_lines

def process_data(data_str):
    # Convert the string data to a list of dictionaries
    data = json.loads(data_str)

    # Dictionary to store the lowest prices for each product
    lowest_prices = {}

    # Iterate over each item in the data
    for item in data:
        product_name = item['product_name']
        price = int(item['price'])
        availability = item.get('availability')  # use get() to safely access 'availability'
        url = item['url']  # get the url from the item

        # Only process the item if the availability is "raktáron"
        if availability and availability.lower() == "raktáron":
            # Update lowest price for the product
            if product_name not in lowest_prices:
                lowest_prices[product_name] = {'prices': [price], 'url': url}
            else:
                lowest_prices[product_name]['prices'].append(price)

    # Calculate the top 3 lowest prices for each product
    for product_name, data in lowest_prices.items():
        prices = data['prices']
        rounded_prices = [round(price / 1.27) for price in prices]
        lowest_prices[product_name]['prices'] = sorted(rounded_prices)[:3]

    # Generate the new version of the data with unique product names and top 3 lowest prices
    new_data = []
    for product_name, data in lowest_prices.items():
        new_data.append({
            "product_name": product_name,
            "lowest_prices": data['prices'],
            "url": data['url']  # include the url in the new data
        })

    return new_data

def generate(data):
        if data is None:
            raise ValueError("Data cannot be None")
        
        chunk_size = 4096  # Adjust chunk size as needed
        yield "[\n"
        for index, item in enumerate(data):
            if item is not None:
                item_str = json.dumps({"product_name": item["product_name"], "lowest_prices": item["lowest_prices"]})
                for i in range(0, len(item_str.encode('utf-8')), chunk_size):
                    yield "  " + item_str[i:i + chunk_size] + (",\n" if index < len(data) - 1 else "")  # Add comma unless it's the last element
        yield "]"

def log_folder_content(folder_path):
    logging.info(f"Listing contents of folder: {folder_path}")
    try:
        with os.scandir(folder_path) as entries:
            for entry in entries:
                if entry.is_file():
                    logging.info(f"File: {entry.name}")
                elif entry.is_dir():
                    logging.info(f"Directory: {entry.name}")
    except OSError as e:
        logging.error(f"Error while listing folder contents: {e}")

api = Blueprint('api', __name__)

@api.route('/ping', methods=['GET'])
def test_server():
    # Check if the server is running
    server_running = True  # Replace this with your actual server status check logic

    # Return a JSON response with the server status
    return jsonify({"server_running": server_running})

@api.route('/keys', methods=['GET'])
def check_api_key():
    # Get the API key from the request headers
    provided_api_key = request.headers.get('shrek_key')

    # Check if the provided API key matches the expected API key
    if is_valid_api_key(provided_api_key):
        return jsonify({"message": "API key is correct"})
    else:
        return jsonify({"message": "API key is incorrect"}), 401  # Return a 401 Unauthorized status

    
#The part where get proxy api route will return a json file

proxy_blueprint = Blueprint('proxy', __name__)


executor = ThreadPoolExecutor()

@proxy_blueprint.route('/get_data', methods=['GET'])
def get_data():
    provided_api_key = request.headers.get('shrek_key')

    if not is_valid_api_key(provided_api_key):
        pass
        #return jsonify({"message" : "API key is incorrect"}), 401 

    spider_runner = SpiderRunner(spider_name='arukereso_all', output_file='Result.json')
    spider_runner.run()

    return "Spider is running asynchronously. The data will be avaiable at /get_final_data"
    # Return a response immediately indicating that the spider is running asynchronously
    
    
@proxy_blueprint.route('/get_final_data', methods=['GET'])
def Get_final_data():
    provided_api_key = request.headers.get('shrek_key')

    if not is_valid_api_key(provided_api_key):
        pass
        #return jsonify({"message" : "API key is incorrect"}), 401 

    # Get the absolute path of the Flask app's root directory
    app_root = os.path.abspath(os.path.dirname(__file__))
    directory = "../heroku_scrapy"
    folder_log = os.path.join(app_root, directory)

    result = "output.jsonl"
    json_path = os.path.join(folder_log, result)
    
    data = process_jsonl(json_path)
    data = process_data(data)

    return Response(generate(data), content_type='text/plain')




@api.route('/start_aprox_scrape', methods=['POST'])
def start_aprox_scrape():
    provided_api_key = request.headers.get('shrek_key')

    if not is_valid_api_key(provided_api_key):
        return jsonify({"message" : "API key is incorrect"}), 401 
    
    # TODO implement the category adding

    # Start the spider in a separate thread
    spider_thread = threading.Thread(target=run_aprox_spider)
    spider_thread.start()

    return "Spider run correctly! The data will available at /get_products_url endpoint"

# Getting only an prox price and url to a category 
@api.route('/get_products_url', methods=['GET'])
def get_products_url():
    provided_api_key = request.headers.get('shrek_key')

    if not is_valid_api_key(provided_api_key):
        return jsonify({"message" : "API key is incorrect"}), 401 
    
    # Checking the category 
    # TODO implement a cetegory differentialization 

    try:
        # Get the absolute path of the Flask app's root directory
        app_root = os.path.abspath(os.path.dirname(__file__))
        directory = "../app/app/heroku_scrapy"
        json_filename = "outputUrl.json"
        json_path = os.path.join( directory, json_filename)

        # Log the contents of the app_root directory
        logging.info(f"Contents of app_root directory ({app_root}): {os.listdir(app_root)}")
        logging.info(f"Contents of app_root + directory  directory ({directory}): {os.listdir(directory)}")


        # Log the full directory path
        full_directory_path = os.path.join(app_root, directory)
        if os.path.exists(full_directory_path):
            logging.info(f"Contents of directory ({full_directory_path}): {os.listdir(full_directory_path)}")
        else:
            logging.error(f"Directory not found: {full_directory_path}")

         # Log the full JSON path
        logging.info(f"Full JSON path: {json_path}")

        # Check if the file exists
        if not os.path.exists(json_path):
            return jsonify({"error": "JSON file not found"}), 404

        # Function to stream JSON data from file
        def generate():
            with open(json_path, 'r', encoding='utf-8') as f:
                for line in f:
                    yield line.rstrip() + '\n'

        return Response(stream_with_context(generate()), content_type='application/json')

    except Exception as e:
        logging.error(f"Error processing JSON data: {str(e)}")
        return jsonify({"error": "Error processing JSON data"}), 500

    
@api.route('/start_url_scrape', methods=['POST'])
def start_url_scrape():
    provided_api_key = request.headers.get('shrek_key')

    if not is_valid_api_key(provided_api_key):
        return jsonify({"message" : "API key is incorrect"}), 401 
    
    data = request.get_json()
    urls = data.get('urls', [])
    

    current_directory = os.getcwd()
    logging.info(f"Current Working Directory: {current_directory}")

    # Run inside the app 

    # Only for testing purpses
    if not urls:
        urls = ["https://www.arukereso.hu/nyomtato-patron-toner-c3138/canon/pg-545xl-black-bs8286b001aa-p197948661/"]
        #return jsonify({"error: " : "No URLS prvided "}), 423

    
    # Start the spider in a separate thread
    spider_thread = threading.Thread(target=partial(run_url_spider, urls=urls))
    spider_thread.start()
    return "Spider run correctly! The data will available at /get_products_url endpoint"


@api.route('/get_url_scrape', methods=["GET"])
def get_url_scrape():
    provided_api_key = request.headers.get('shrek_key')

    if not is_valid_api_key(provided_api_key):
        return jsonify({"message" : "API key is incorrect"}), 401 
    
    try:
        # Get the absolute path of the Flask app's root directory
        app_root = os.path.abspath(os.path.dirname(__file__))
        directory = "../app/app/heroku_scrapy"
        json_filename = "marketPrices.json"
        json_path = os.path.join( directory, json_filename)

        # Log the contents of the app_root directory
        logging.info(f"Contents of app_root directory ({app_root}): {os.listdir(app_root)}")
        logging.info(f"Contents of app_root + directory  directory ({directory}): {os.listdir(directory)}")

        logging.info(f"Content of JSONpath:  {json_path}" )

        # Check if the file exists
        if not os.path.exists(json_path):
            return jsonify({"error": "JSON file not found"}), 404

        # Function to stream JSON data from file
        def generate():
            with open(json_path, 'r', encoding='utf-8') as f:
                for line in f:
                    yield line.rstrip() + '\n'

        return Response(stream_with_context(generate()), content_type='application/json')

    except Exception as e:
        logging.error(f"Error processing JSON data: {str(e)}")
        return jsonify({"error": "Error processing JSON data"}), 500
