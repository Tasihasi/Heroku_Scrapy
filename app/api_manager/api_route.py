from flask import Blueprint, jsonify, request, Response, send_file
import xml.etree.ElementTree as ET
import os
from .auth import valid_api_key, mach_apiKey_to_customer, getting_raw_data
from .scrapy_manager import newest_raw_data
from .api_proxy import gather_proxy_data
from .data_retrieve import get_data_from_scrapy, get_proxies
from concurrent.futures import ThreadPoolExecutor  # For async execution

#from auth import Test

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
    path = "../heroku_scrapy/result.xml"

    # Check if the file exists at the specified path
    if os.path.exists(path):
        # If the file exists, return the file as an attachment
        return send_file(path, mimetype='application/xml', as_attachment=True)
    else:
        # If the file doesn't exist yet, return a message indicating its unavailability
        return "Data is not yet available. Please try again later."
    


