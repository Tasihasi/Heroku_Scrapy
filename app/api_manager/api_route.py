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


def jsonL_to_xml(jsonl_file, xml_file, required_keys=None):
    if required_keys is None:
        required_keys = set()

    # Open JSONL file for reading
    with os.fdopen(os.open(jsonl_file, os.O_RDONLY), 'r', encoding="utf-8") as jsonl_file:
        fcntl.flock(jsonl_file.fileno(), fcntl.LOCK_SH)
        # locking the file 

        # Read all lines into a list, excluding the last line
        json_lines = list(jsonl_file)[:-1]

        # Create the root element of the XML document
        root = ET.Element("items")

        # Loop through each line in the JSONL file
        for line_number, line in enumerate(jsonl_file, start=1):
            try:
                # Parse JSON from the line
                json_data = json.loads(line)

                # Check if all required keys are present in the JSON data
                if all(key in json_data for key in required_keys):
                    # Create an XML element for each JSON object
                    element = ET.SubElement(root, "item")

                    # Add sub-elements for each key-value pair in the JSON object
                    for key, value in json_data.items():
                        logging.info(f"----- the key: {key}   -----  value : {value}--------")
                        if value is not None and value != "" and value != "\n":
                            sub_element = ET.SubElement(element, key)
                            sub_element.text = str(value).strip()
                else:
                    logging.warning(f"Incomplete item on line {line_number}: Missing required keys")

            except json.JSONDecodeError as e:
                logging.error(f"Error on line {line_number}: {e}")

    # Convert the ElementTree to an XML string
    xml_string = ET.tostring(root, encoding='utf-8').decode('utf-8')

    

    # Remove incomplete last <item> element
    xml_string = remove_incomplete_last_item(xml_string, required_keys)

    # Fix missing </item> tag
    xml_string = fix_missing_item_tag(xml_string)

    # Write the XML string to the specified file
    with open(xml_file, 'wb') as xml_file:
        xml_file.write(xml_string.encode('utf-8'))


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

def create_empty_xml(file_path):
    # Extract the directory path from the file path
    directory = os.path.dirname(file_path)

    # Create the directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)

    # Create the root element for the XML document
    items = ET.Element("items")
    item = ET.SubElement(items, "item")

    # Create an ElementTree object from the root element
    tree = ET.ElementTree(items)

    # Write the XML document to the specified file path
    with open(file_path, 'wb') as file:
        tree.write(file)

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





@proxy_blueprint.route('/preparing_xml', methods=['GET'])
def preparing_xml():

    # Retrieve the API key from the request headers
    api_key = request.headers.get('API-Key')

    # Retrieve the Clondike_Key from the environment variables
    valid_api_key =  os.environ.get('Clondike_Key')

    log_folder_content("app/heroku_scrapy")

    current_directory = os.getcwd()
    logging.info(f"Current working directory:  haaagh :: {current_directory}")
    directory_contents = os.listdir(".")
    logging.info(f"Current directory dir:  {directory_contents}")

    


    

    directory = "app/heroku_scrapy"
    filename = "output.jsonl"
    result = "resulting.xml"


    path = os.path.join(os.getcwd(), directory, result)

    #if os.path.exists(path):
        #return send_file(path, as_attachment=True)


    

    jsonl_path = os.path.join(directory, filename)
    xml_path = os.path.join(directory, result)

    create_empty_xml(xml_path)


    # Log the contents of the folder
    log_folder_content(directory)

    try:
        jsonL_to_xml(jsonl_path, xml_path)
    except Exception as e:
        logging.error(f"Error converting JSONL to XML: {str(e)}")
        return "Error during file conversion please try again later!"

    if os.path.exists(path):
        #return send_file(path, as_attachment=True)
        return "the file is ready"
      
    return "path dose not exist ---- >:"



@proxy_blueprint.route('/get_final_data', methods=['GET'])
def Get_final_data():

    # Retrieve the API key from the request headers
    api_key = request.headers.get('API-Key')

    # Retrieve the Clondike_Key from the environment variables
    valid_api_key = os.environ.get('Clondike_Key')

    if api_key != valid_api_key:
        return "Api key is not valid ---- :("

    directory = "app/heroku_scrapy"
    result = "output.jsonl"
    xml_path = os.path.join(directory, result)
    log_folder_content(directory)

    try:
        # Read and strip values from the JSONL file
        stripped_lines = strip_values_in_jsonl(xml_path)

        # Create a new stripped JSONL file
        stripped_jsonl_path = os.path.join(directory, "stripped_output.jsonl")
        with open(stripped_jsonl_path, 'w', encoding="utf-8") as stripped_file:
            stripped_file.writelines(stripped_lines)

        # Convert the stripped JSONL file to XML (you can use your existing logic here)
        jsonL_to_xml(stripped_jsonl_path, "resulting.xml")

        # Send the resulting XML file
        return send_file("resulting.xml", as_attachment=True)

    except FileNotFoundError as e:
        logging.error(f"FileNotFoundError: {e}")
        return "File not found", 404
    

    
