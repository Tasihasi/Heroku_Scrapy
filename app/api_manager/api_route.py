from flask import Blueprint, jsonify, request, Response, send_file, make_response, current_app
import xml.etree.ElementTree as ET
import json
import os
import sys
import logging
from .auth import valid_api_key, mach_apiKey_to_customer, getting_raw_data
from .scrapy_manager import newest_raw_data
from .api_proxy import gather_proxy_data
from .data_retrieve import get_data_from_scrapy, get_proxies
from concurrent.futures import ThreadPoolExecutor  # For async execution
import fcntl



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
def process_jsonl(input_path, output_filename="BigOutput.jsonl", required_keys=["price", "availability", "competitor", "product_name", "url"]):
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
        #for record in filtered_data:
            #if "availability" in record:
                #del record["availability"]

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


import json

def process_data(data_str):
    # Convert the string data to a list of dictionaries
    data = json.loads(data_str)

    # Dictionary to store the lowest prices for each product
    lowest_prices = {}

    # Iterate over each item in the data
    for item in data:
        product_name = item['product_name']
        price = int(item['price'])
        url = item["url"]

        if 'availability' in item and  "rakt" in item["availability"] : # (item['availability'] == "raktáron" or item["availability"] == "rakt\u00e1ron"):
            # Update lowest price for the product
            # TODO The prices diseapr here !!!! 
            if product_name not in lowest_prices:
                lowest_prices[product_name] = {'prices': [price], 'url': item['url']}
                logging.info(f"this url is added to the lowest prices :  {item}")
            else:
                lowest_prices[product_name]["prices"].append(price)

    
    logging.info(f"here is the lowest prices variable after adding items :  {lowest_prices}")
    # Calculate the top 3 lowest prices for each product
    for product_name, product_info in lowest_prices.items():
        if 'prices' in product_info and isinstance(product_info['prices'], list):
            rounded_prices = [round(price / 1.27) for price in product_info['prices']]
            lowest_prices[product_name]['prices'] = sorted(rounded_prices)[:3]

    # Generate the new version of the data with unique product names and top 3 lowest prices
    new_data = []
    for product_name, product_info in lowest_prices.items():
        if 'prices' in product_info and isinstance(product_info['prices'], list):
            new_data.append({
                "product_name": product_name,
                "lowest_prices": product_info['prices'],
                "url": product_info['url']  # add the URL to the new data
            })

    return new_data





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

@api.route('/check_api_key', methods=['GET'])
def check_api_key():
    # Get the API key from the request headers
    provided_api_key = request.headers.get('Authorization')

    # Check if the provided API key matches the expected API key
    if valid_api_key(provided_api_key):
        return jsonify({"message": "API key is correct"})
    else:
        return jsonify({"message": "API key is incorrect"}), 401  # Return a 401 Unauthorized status


@api.route('/get_raw_data', methods = ['GET'])
def get_raw_data():
    provided_api_key = request.headers.get('Authorization')

    if getting_raw_data(provided_api_key):
        return newest_raw_data(provided_api_key)
    
    elif valid_api_key(provided_api_key):
        return jsonify({"message" : "The corresponding customer status is inactive"})

    else:
        return jsonify({"message" : "The api key provided is incorrect."})

    
#The part where get proxy api route will return a json file

proxy_blueprint = Blueprint('proxy', __name__)


executor = ThreadPoolExecutor()

@proxy_blueprint.route('/get_data', methods=['GET'])
def get_data():
    def process():
        # Assuming get_data_from_scrapy() returns the path to the XML file
        xml_file_path = get_data_from_scrapy()

        if xml_file_path:
            # Specify the mimetype as 'application/xml'
            return send_file(xml_file_path, mimetype='application/xml', as_attachment=True)
        
        return "Spider run failed."
    
     # Submit the 'process' function to the executor for asynchronous execution
    future = executor.submit(process)

    # Return a response immediately indicating that the spider is running asynchronously
    return "Spider is running asynchronously. The data will be avaiable at /get_final_data"
    


@proxy_blueprint.route('/get_proxy', methods=['GET'])
def get_proxies():
    # Assuming get_data_from_scrapy() returns the path to the XML file
    xml_file_path = get_proxies()

    if xml_file_path:
        # Specify the mimetype as 'application/xml'
        return send_file(xml_file_path, mimetype='application/xml', as_attachment=True)
    
    return "Spider run failed."


@proxy_blueprint.route('/get_final_data', methods=['GET'])
def Get_final_data():

    # Retrieve the API key from the request headers
    api_key = request.headers.get('API-Key')

    # Retrieve the Clondike_Key from the environment variables
    valid_api_key = os.environ.get('Clondike_Key')

    if api_key != valid_api_key:
        return "Api key is not valid ---- :("
    
    current_directory = os.getcwd()
    #logging.info(f"Current Working Directory: {current_directory}")

    

    # Get the absolute path of the Flask app's root directory
    app_root = os.path.abspath(os.path.dirname(__file__))
    directory = "../heroku_scrapy"
    folder_log = os.path.join(app_root, directory)
    logging.info(f"---------- {folder_log}  -------------")
    #log_folder_content(folder_log)

    result = "output.jsonl"
    json_path = os.path.join(folder_log, result)
    
    #logging.critical("---------------------   The data being sent -----------")
    data = process_jsonl(json_path)

    logging.critical(f" here is the data being logged Before processing it :   {data}")

    data = process_data(data)


    logging.critical(f" here is the data being logged :   {data}")

    # Log the length of the data in bytes
    #logging.info(f"Data length: {sys.getsizeof(data)} bytes")
    #logging.info("---------------------------------------------")


    # Function to stream data in chunks
    
    def generate(data):
        if data is None:
            raise ValueError("Data cannot be None")
        
        chunk_size = 4096  # Adjust chunk size as needed
        yield "[\n"
        for index, item in enumerate(data):
            if item is not None:
                item_str = json.dumps({
                    "product_name": item["product_name"], 
                    "lowest_prices": item["lowest_prices"],
                    "url": item["url"]  # include the url
                })
                for i in range(0, len(item_str.encode('utf-8')), chunk_size):
                    yield "  " + item_str[i:i + chunk_size] + (",\n" if index < len(data) - 1 else "")  # Add comma unless it's the last element
        yield "]"

    return Response(generate(data), content_type='text/plain')

    

        # Optionally, you can yield the whole JSON array by wrapping it in brackets
        # yield "[" + ",".join(generate()) + "]"



    json_path = os.path.join(folder_log, process_jsonl(json_path)) 
    # if procces_jsonl return wit an exception than the code crashes
    

    try:

        #json_file = strip_values_in_jsonl(json_path)
        # Send the resulting XML file
        return send_file(json_path, as_attachment=True)

    except FileNotFoundError as e:
        try:

            directory = "."
            log_folder_content(directory)
            json_path = os.path.join(directory, result)
            return send_file(result, as_attachment=True)
        except FileNotFoundError as e:
            logging.error(f"FileNotFoundError: {e}")
            return "File not found", 404
        
    
    

    
