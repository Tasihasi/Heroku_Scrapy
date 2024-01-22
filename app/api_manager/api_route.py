from flask import Blueprint, jsonify, request, Response, send_file, make_response
import xml.etree.ElementTree as ET
import json
import os
import logging
from .auth import valid_api_key, mach_apiKey_to_customer, getting_raw_data
from .scrapy_manager import newest_raw_data
from .api_proxy import gather_proxy_data
from .data_retrieve import get_data_from_scrapy, get_proxies
from concurrent.futures import ThreadPoolExecutor  # For async execution



def json2xml(json_obj, line_padding=""):
    result_list = list()

    json_obj_type = type(json_obj)

    if json_obj_type is list:
        for sub_elem in json_obj:
            result_list.append(json2xml(sub_elem, line_padding))

        return "\n".join(result_list)

    if json_obj_type is dict:
        for tag_name in json_obj:
            sub_obj = json_obj[tag_name]
            result_list.append("%s<%s>" % (line_padding, tag_name))
            result_list.append(json2xml(sub_obj, "\t" + line_padding))
            result_list.append("%s</%s>" % (line_padding, tag_name))

        return "\n".join(result_list)

    return "%s%s" % (line_padding, json_obj)

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

api_key = 12345

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

    

#curl -X POST -H "Authorization: Bearer 12345" http://127.0.0.1:5000/check_api_key
# the tester call


#The part where get proxy api route will return a json file

proxy_blueprint = Blueprint('proxy', __name__)

@proxy_blueprint.route('/get_sth', methods=['GET'])
def get_sth():
    # Call a function or script to gather the JSON file with proxies
    # Replace 'gather_proxy_data()' with the actual function or script
    proxy_data = gather_proxy_data()

    # Check if proxy data is available
    if proxy_data:
        return jsonify(proxy_data)
    else:
        return jsonify({"message": "No proxy data available"}), 404  # Return a 404 Not Found status


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
    valid_api_key =  os.environ.get('Clondike_Key')

    log_folder_content("app/heroku_scrapy")

    current_directory = os.getcwd()
    logging.info(f"Current working directory:  haaagh :: {current_directory}")
    directory_contents = os.listdir(".")
    logging.info(f"Current directory dir:  {directory_contents}")

    

    if api_key != valid_api_key:
        return "Invalid API Key ! :("
    

    directory = "app/heroku_scrapy"
    filename = "output.jsonl"
    path = os.path.join(os.getcwd(), directory, filename)

    # Log the contents of the folder
    log_folder_content(directory)

    # Check if the file exists at the specified path
    if not os.path.exists(path):
        return "Data is not here ----"

    # Read JSON Lines file
    with open(path, 'r') as jsonl_file:
        lines = jsonl_file.readlines()

    # Create root element for XML
    root = ET.Element("root")
    items_element = ET.SubElement(root, "items")  # New line to add <items> element

    # Loop through each line in the JSON Lines file
    # Loop through each line in the JSON Lines file
    for line_number, line in enumerate(lines, start=1):
        # Try to parse each JSON object
        try:
            data = json.loads(line)

            logging.info(f"-------  data: {data} ------------------")

            # Check if all required attributes are present
            if (
                all(attr in data for attr in ['price', 'availability', 'competitor', 'product_name']) 
                and data['availability'] and data['availability'].strip() != ''  # Check for non-empty availability
                and data['competitor'] and data['competitor'].strip() != ''  # Check for non-empty competitor
            ):
                # Create an XML element for each JSON object
                # item_element = ET.SubElement(items_element, "item")  # Use items_element as the parent

                # Convert JSON to XML using the json2xml function
                xml_str = json2xml(data)

                # Parse the XML string and append it to the items_element
                xml_elem = ET.fromstring(xml_str)
                items_element.append(xml_elem)
        except json.JSONDecodeError as e:
            # If parsing as JSON fails, log the error and skip to the next line
            logging.error(f"Error decoding JSON at line {line_number}: {e}. Skipped line: {line}")
            continue
        except Exception as e:
            # Handle other exceptions if needed
            logging.error(f"An unexpected error occurred at line {line_number}: {e}. Skipped line: {line}")
            continue

    # Create XML content as a string
    xml_content = ET.tostring(root, encoding="utf-8", method="xml")

    # Create a response with the XML content
    response = make_response(xml_content)
    response.headers["Content-Type"] = "application/xml"
    response.headers["Content-Disposition"] = "attachment; filename=Result.xml"

    return response
         
    return "Unhandled Error "


