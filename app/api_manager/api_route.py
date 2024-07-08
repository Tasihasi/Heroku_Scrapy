from flask import Blueprint, jsonify, request, Response, send_file, stream_with_context
import xml.etree.ElementTree as ET
import json
import os
import logging
from .auth import valid_api_key, getting_raw_data
from .scrapy_manager import newest_raw_data
from .data_retrieve import get_data_from_scrapy, get_proxies, run_data_man, get_top_5_products,run_aprox_spider, run_url_spider
#from .run_data_manipulate import run_data_man
from concurrent.futures import ThreadPoolExecutor  # For async execution
from datetime import datetime, timedelta
import requests
import threading
from functools import partial

#from .heroku_scrapy.spiders.url_crawl import UrlCrawlSpider


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
    logging.info(f"here is the data:  {data}" )
    data = process_data(data)

    logging.critical(data)

    # Log the length of the data in bytes
    #logging.info(f"Data length: {sys.getsizeof(data)} bytes")
    #logging.info("---------------------------------------------")


    # Function to stream data in chunks
    
    

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
        


# TODO  have to differentiate between files and product categories !!!
@api.route('/get_processed_data', methods=['GET'])
def get_processed_data():
    client_api_key = request.args.get('api_key')
    home_url =  os.getenv("home_url")


    if client_api_key is None:
        return jsonify({"message" : "No apikey provided."})
    

    shrek_key = os.getenv("shrek_api_key")

    # Make an API call to the home URL's list files endpoint
    headers = {"shrek_key" : shrek_key}
    
    response = requests.get(f"{home_url}/list_files", headers=headers)

    if response.status_code != 200:
        logging.error(f"Problem happened getting files listed from Google Drive. Status code:   {response.status_code}")
        return jsonify({"message" : "Problem happened!"})
    
     # Get the list of files
    files = response.json().get('files', [])

    # Search for a file named with a date from the past week
    for i in range(1, 8):
        date_to_find = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        for file in files:
            if file['name'] == date_to_find:
                print(f"Found file with name {date_to_find}")

    logging.info(f"here is the file id:  {file['id']}")

    response = requests.get(f"{home_url}/get_file/{file['id']}", headers=headers) 


    if response.status_code != 200:
        logging.error(f"Problem happened retrieving the  file  from Google Drive. Status code:   {response.status_code}")
        return jsonify({"message" : "Problem happened!"})
    

    processed_data = (response.text)

    if  not processed_data:
        return jsonify({"message" : "The data processing failed!"})
    
    # TODO  make the response simple 
    #return processed_data
    logging.info(f"Here is the data that being sent:  {processed_data}")
    return Response(generate(processed_data), content_type='text/plain')
    
@api.route('/customer_data_process', methods=['GET']) 
def get_customer_data():
    client_api_key = request.args.get('shrek_key')
    home_url =  os.getenv("home_url")

    if client_api_key is None:
        return jsonify({"message" : "No apikey provided."})
    

    shrek_key = os.getenv("shrek_api_key")

    # Check if the provided API key matches the expected API key

    if client_api_key != shrek_key:
        return jsonify({"message" : "API key is incorrect"}), 401  # Return a 401 Unauthorized status
    
    success = run_data_man(".business_logic/")

    if success:
        return jsonify({"message" : "Data processing was successful!"})
    
    return jsonify({"message" : "Data processing failed!"})
        
@api.route('/get_business_logic_data', methods=['GET'])
def get_business_logic_data(file_name : str = "customer_min_prices.xml"):

    client_api_key = request.headers.get('shrek_key')
    home_url =  os.getenv("home_url")


    if client_api_key is None:
        return jsonify({"message" : "No apikey provided."})
    

    shrek_key = os.getenv("shrek_api_key")

    if client_api_key != shrek_key:
        return jsonify({"message" : "API key is incorrect"}), 401  # Return a 401 Unauthorized status

    # Make an API call to the home URL's list files endpoint

    #requested_file = request.view_args['file_name']
    requested_file = file_name

    script_dir = os.path.dirname(os.path.abspath(__file__))

    file_path = os.path.join(script_dir, "business_logic", requested_file)

    if not os.path.exists(file_path):  
        logging.error(f"The file {file_path} does not exist.")
        return jsonify({"message" : "The file does not exist."})
    
    logging.info(f"Sending file from business logic: {file_path}")
    return send_file(file_path, as_attachment=True)


@api.route('/get_top_5_products', methods=['GET'])
def get_top_5_products_api():

    def xml_to_dict(elem):
        """Recursively convert an XML element to a dictionary."""
        # Base case: If the element has no children, return its text or an empty string
        if not elem:
            return elem.text if elem.text else ""
        result = {}
        for child in elem:
            # Recursively process child elements
            child_result = xml_to_dict(child)
            # Handle multiple children with the same tag
            if child.tag in result:
                if type(result[child.tag]) is list:
                    result[child.tag].append(child_result)
                else:
                    result[child.tag] = [result[child.tag], child_result]
            else:
                result[child.tag] = child_result
        # Include element's attributes in the result
        result.update(('@' + k, v) for k, v in elem.attrib.items())
        return result

    

    """
    client_api_key = request.headers.get('shrek_key')
    home_url =  os.getenv("home_url")


    if client_api_key is None:
        return jsonify({"message" : "No apikey provided."})
    

    shrek_key = os.getenv("shrek_api_key")

    if client_api_key != shrek_key:
        return jsonify({"message" : "API key is incorrect"}), 401
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))

    file_path = os.path.join(script_dir, "business_logic")

    logging.info(f"Sending file from business logic: {file_path}")

    isData = get_top_5_products(file_path)

    if isData is None:
        return jsonify({"message" : "Data processing failed!"}, 500) 
    
    # Checking if path exists

    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, "business_logic", "top_5_products.xml")

    if not os.path.exists(file_path):
        logging.error(f"The file {file_path} does not exist.")
        return jsonify({"message" : "The file does not exist."}, 404)

    # Loading to memory the data

    # Path to your XML file
    xml_file_path = file_path

    # Parse the XML file and get the root element
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    # Convert the XML data to a JSON string
    dict_data = xml_to_dict(root)
    json_data = json.dumps(dict_data, indent=4)

    # Create a custom response
    response = Response(json_data, mimetype='application/json')

    # Set headers to prompt for download
    response.headers["Content-Disposition"] = "attachment; filename=top5_products.json"

    # Return the JSON data  as attachment

    return response


@api.route('/start_aprox_scrape', methods=['GET'])
def start_aprox_scrape():

    # Start the spider in a separate thread
    spider_thread = threading.Thread(target=run_aprox_spider)
    spider_thread.start()

    return "Spider run correctly! The data will available at /get_products_url endpoint"

# Getting only an prox price and url to a category 
@api.route('/get_products_url', methods=['GET'])
def get_products_url():
    """
    client_api_key = request.headers.get('shrek_key')
    home_url =  os.getenv("home_url")


    if client_api_key is None:
        return jsonify({"message" : "No apikey provided."})
    

    shrek_key = os.getenv("shrek_api_key")

    if client_api_key != shrek_key:
        return jsonify({"message" : "API key is incorrect"}), 401  # Return a 401 Unauthorized status
    
        
    """
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

    
@api.route('/start_url_scrape', methods=['POST', "GET"])
def start_url_scrape():
    
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
