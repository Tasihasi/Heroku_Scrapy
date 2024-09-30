from flask import Blueprint, jsonify, request
from .auth import is_valid_api_key
from .data_retrieve import   SpiderRunner, RetriveData
import logging, os

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
        return jsonify({"message" : " Unauthorized : API key is incorrect"}), 401  # Return a 401 Unauthorized status

@api.route('/run_spider', methods = ["GET"])
def run_spider():
    provided_api_key = request.headers.get('shrek_key')

    if not is_valid_api_key(provided_api_key):
        return jsonify({"message" : " Unauthorized : API key is incorrect"}), 401 

    provided_spider_name = request.json.get("spider_name")
    provided_output_name = request.json.get("output_name")

    if not provided_spider_name:
        return jsonify({"message" : "No provided spider name"}), 403
    
    if not provided_output_name:
        return jsonify({"message" : "No provided output name"}), 403


    provided_category = request.json.get("category")
    provided_urls = request.json.get("urls")

    logging.info("Running spider")
    logging.info(f"Changed working directory to: {os.getcwd()} in api_route")


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
        return jsonify({"message" : " Unauthorized : API key is incorrect"}), 401 
    
    if not provided_file_name:
        return jsonify({"message" : "Missing file name"}), 403
    
    provided_file_name = request.headers.get("file_name")

    retriever = RetriveData(provided_file_name)  # Replace with your actual file name
    return retriever.get_file()
