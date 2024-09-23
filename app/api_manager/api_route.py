from flask import Blueprint, jsonify, request, Response, send_file, stream_with_context
import xml.etree.ElementTree as ET
import json
import os
import logging
from .auth import is_valid_api_key
from .data_retrieve import   SpiderRunner, RetriveData
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


# TODO  if the spider that requesries additional settings dose not have the provided arguments?
@api.route('/run_spider', methods = ["GET"])
def run_spider():
    provided_api_key = request.headers.get('shrek_key')

    if not is_valid_api_key(provided_api_key):
        return jsonify({"message" : "API key is incorrect"}), 401 

    provided_spider_name = request.json.get("spider_name")
    provided_output_name = request.json.get("output_name")

    if not provided_spider_name:
        return jsonify({"message" : "No provided spider name"}), 403
    
    if not provided_output_name:
        return jsonify({"message" : "No provided output name"}), 403


    provided_category = request.json.get("category")
    provided_urls = request.json.get("urls")

    spider_runner = SpiderRunner(spider_name=provided_spider_name, output_file=provided_output_name, category = provided_category, urls= provided_urls)

    success = spider_runner.run()

    if success == -1:
        return jsonify({"message" : f"There is no such spider: spider name : {provided_spider_name}"}), 404    

    if success == 0:
        return jsonify({"message" : f"There was an error running this spider: {provided_spider_name}"}), 500
    
    return jsonify({"message" : f"Spider runs successfully spider name: {provided_spider_name}, output_name: {provided_output_name}"}), 200


@api.route('/retrive_file', methods = ["GET"])
def retrive_file():
    provided_api_key = request.json.get('shrek_key')

    if not is_valid_api_key(provided_api_key):
        return jsonify({"message" : "API key is incorrect"}), 401 
    
    if not provided_file_name:
        return jsonify({"message" : "Missing file name"}), 403
    
    provided_file_name = request.headers.get("file_name")

    retriever = RetriveData(provided_file_name)  # Replace with your actual file name
    return retriever.get_file()
