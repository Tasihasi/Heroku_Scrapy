from flask import Blueprint, jsonify, request, Response, send_file, make_response, current_app
import xml.etree.ElementTree as ET
import json
import os
import logging
from .auth import valid_api_key, mach_apiKey_to_customer, getting_raw_data
from .scrapy_manager import newest_raw_data
from .api_proxy import gather_proxy_data
from .data_retrieve import get_data_from_scrapy, get_proxies
from concurrent.futures import ThreadPoolExecutor  # For async execution
import fcntl

def fix_missing_item_tag(xml_string):
    # Check if the XML string ends with </item>
    if not xml_string.strip().endswith('</item>'):
        # Append </item> if it's missing
        xml_string += '</item>'
    return xml_string

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
    logging.info(f"Current Working Directory: {current_directory}")


    logging.info('File name :    ', os.path.basename(__file__))
    logging.info('Directory Name:     ', os.path.dirname(__file__))

    # Get the absolute path of the Flask app's root directory
    app_root = os.path.abspath(os.path.dirname(__file__))
    directory = "."
    folder_log = os.path.join(app_root, directory)
    logging.info(f"---------- {folder_log}  -------------")
    log_folder_content(app_root)

    #directory = os.path.join(current_app.root_path, "app/heroku_scrapy")
    directory = "."
    result = "output.jsonl"
    json_path = os.path.join(directory, result)
    logging.info("----------  app/heroku_scrapy -------------")
    log_folder_content(directory)

    directory = "./app"
    json_path = os.path.join(directory, result)
    logging.info(f"-----------------------   {directory} -------------------- ")
    log_folder_content(directory)

    directory = "./app/heroku_scrapy"
    logging.info(f"-----------------------   {directory} -------------------- ")
    log_folder_content(directory)
    json_path = os.path.join(directory, result)

    try:

        json_file = strip_values_in_jsonl(json_path)
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
    

    
