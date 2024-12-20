from flask import Blueprint, jsonify, send_file, send_from_directory, Response, stream_with_context, request
import requests
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from io import BytesIO
import io
from .google_drive_api_auth import Get_drive_service
import logging
from googleapiclient.errors import HttpError
from ..auth import is_valid_api_key
import json
import os

google_drive_api = Blueprint('google_drive_api', __name__)

# Lists the available files in the google drive
@google_drive_api.route('/list_files', methods=['GET'])
def list_files():
    logging.info("List files api endpoint triggered")

    request_api_key = request.headers.get('shrek_key')

    if not check_inner_api_key(request_api_key):
        return jsonify({'error': 'Invalid API key'}), 403
    

    try:
        # Get authenticated Drive API service
        drive_service = Get_drive_service()

        logging.info("Successfully authenticated with Google Drive API")

        # Call Drive API to list files
        results = drive_service.files().list(pageSize=10).execute()
        items = results.get('files', [])

        if not items:
            return jsonify({'message': 'No files found'})
        else:
            # Extract file names
            files_info = [{'name': item['name'], 'id': item['id']} for item in items]
            return jsonify({'files': files_info})
    
    except Exception as e:
        logging.error("Authentication failed or an error occurred: {}".format(str(e)))
        return jsonify({'error': 'Authentication failed or an error occurred'}), 500


# TODO no api key checker here
@google_drive_api.route('/get_file/<file_id>', methods=['GET'])
def get_file(file_id):
    provided_api_key = request.headers.get('shrek_key')

    if not is_valid_api_key(provided_api_key):
        return jsonify({"message" : " Unauthorized : API key is incorrect"}), 401 

    def send_large_file(file_content : BytesIO, file_metadata ):
        file_content.seek(0)
        data = file_content.getvalue()
        file_size = len(data)
        response = Response(
            file_content,
            mimetype=file_metadata['mimeType'],
            headers={
                "Content-Disposition": f"attachment; filename={file_metadata['name']}",
                "Content-Length": file_size
            }
        )

        #logging.info("File content: " + data.decode('utf-8'))
        return response

    # Get authenticated Drive API service
    drive_service = Get_drive_service()

    try:
        # Call the Drive API to retrieve the file metadata
        file_metadata = drive_service.files().get(fileId=file_id).execute()

        # Create a file-like object to store the file content
        file_content = io.BytesIO()

        # Request the file content from Google Drive
        request = drive_service.files().get_media(fileId=file_id)
        downloader = MediaIoBaseDownload(file_content, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()

        # Rewind the file-like object to the beginning
        file_content.seek(0)

        file_content.seek(0)
        content = file_content.read()

        # Convert the bytes to a string for logging
        #content_str = content.decode('utf-8')

        #logging.info("File content: " + content_str)
        return send_large_file(file_content, file_metadata)
        
    except Exception as e:
        # Handle any errors that occur during the process
        print("An error occurred:", e)
        return "Error occurred while retrieving the file.", 500
    
    

@google_drive_api.route('/create_file/<file_name>/<file_mimeType>/<force_update>', methods=['POST'])
def create_file( file_name, file_mimeType, force_update = 0):
    from flask import request
    
    logging.info("Create file api endpoint triggered")

    # Checking the api key

    request_api_key = request.headers.get('shrek_key')


    if not is_valid_api_key(request_api_key):
        return jsonify({"message" : " Unauthorized : API key is incorrect"}), 401

    if not file_name or not file_mimeType:
        return jsonify({'error': 'File name and MIME type are required.'}), 400

    # modify the MIME type if necessary

    if file_mimeType == "text":
        file_mimeType = "text/plain"
    elif file_mimeType == "ipynb":
        file_mimeType = "application/x-ipynb+json"
    elif file_mimeType == "csv":
        file_mimeType = "text/csv"
    elif file_mimeType == "gzip":
        file_mimeType = "application/gzip"

    home_url = os.getenv('home_url')

    # Make a GET request to the list_files endpoint
    response = requests.get(f'{home_url}/list_files')

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        files = response.json()["files"]

        # Check if the file name already exists
        file_id = None
        for file in files:
            if file_name == file['name']:
                file_id = file["id"]
                if force_update != 1:
                    return jsonify({'error': 'File name already exists.'}), 400

        # Delete the file if it already exists and force_update is set to 1
        if force_update == 1 and file_id is not None:
            delete_file(file_id)
    logging.info("File name does not exist. Proceeding to create the file.")

    try:
        # create drive api client
        service = Get_drive_service()

        file_metadata = {"name": file_name,
                        "mimeType": file_mimeType,
                         
                         }
        
         # Get the content from the POST request
        content = request.get_data()
        # Create a file-like object from the content
        fh = io.BytesIO(content)

        # Create a media object from the file-like object
        media = MediaIoBaseUpload(fh, mimetype=file_mimeType)
        # pylint: disable=maybe-no-member
        file = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )

        logging.info(f"File created successfully: {file.get('id')}")

        return jsonify({'file_id': file.get('id')})

    except HttpError as error:
        print(f"An error occurred: {error}")
        file = None

    return file.get("id")

@google_drive_api.route('/delete_file/<file_id>', methods=['GET'])
def delete_file( file_id):
     
    request_api_key = request.headers.get('shrek_key')

    if not is_valid_api_key(request_api_key):
        return jsonify({"message" : " Unauthorized : API key is incorrect"}), 401

    if not file_id:
        return jsonify({'error': 'File ID is required.'}), 400
     
    home_url = os.getenv('home_url')

    # Make a GET request to the list_files endpoint
    response = requests.get(f'{home_url}/list_files')

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        files = response.json()['files']

        # Check if the file name does not exist
        file_exists = False
        for file in files:
            if file_id == file['id']:
                file_exists = True
                break

        if not file_exists:
            return jsonify({'error': 'File does not exist.'}), 400
     
     
     # Get authenticated Drive API service
    drive_service = Get_drive_service()

    try:
        drive_service.files().delete(fileId=file_id).execute()
        return jsonify("File deleted successfully.")
    except HttpError as e:
        # Handle HTTP errors
        error_message = json.loads(e.content)['error']['message']
        if e.resp.status == 404:
            # File not found error
            return jsonify({'error': f'File with ID {file_id} not found.'}), 404
        else:
            # Other HTTP errors
            return jsonify({'error': f'An HTTP error occurred: {error_message}'}), e.resp.status

    except Exception as e:
        # Handle other exceptions
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@google_drive_api.route('/run_script', methods=['GET'])
def run_script():
    from flask import request

    logging.info("Run script api endpoint triggered")   

    request_api_key = request.headers.get('shrek_key')
    file_id = request.headers.get('file_id')

    if not is_valid_api_key(request_api_key):
        return jsonify({"message" : " Unauthorized : API key is incorrect"}), 401


    # Authenticate with Google Drive API using credentials JSON file
    drive_service = Get_drive_service()

    logging.info("Successfully authenticated with Google Drive API")

    # Retrieve the script content from Google Drive
    request = drive_service.files().get_media(fileId=file_id)
    script_content = request.execute()

    logging.info("Script content retrieved successfully")

    try:
        compile(script_content, '<string>', 'exec')
    except SyntaxError:
        return "Invalid Python code", 400

    exec(script_content)

@google_drive_api.route('/upload', methods=['POST'])
def upload_file():


    request_api_key = request.headers.get('shrek_key')

    if not is_valid_api_key(request_api_key):
        return jsonify({"message" : " Unauthorized : API key is incorrect"}), 401

    logging.info("Api endpoint triggered")
    try:
        if 'file' not in request.files:
            return 'No file part in the request', 400
        file = request.files['file']
        if file.filename == '':
            return 'No selected file', 400
        if file:
            os.makedirs('uploads', exist_ok=True)
            filename = os.path.join('uploads', (file.filename))
            file.save(filename)
            logging.info(f'File saved as {filename}')
            logging.info(f'Current file path: {os.path.abspath(filename)}')
            return 'File saved successfully', 200
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return 'An error occurred', 500

@google_drive_api.route('/download_uploaded/<file_name>', methods=['GET'])
def download_download_uploaded_file( file_name):

    request_api_key = request.headers.get('shrek_key')

    if not is_valid_api_key(request_api_key):
        return jsonify({"message" : " Unauthorized : API key is incorrect"}), 401

    logging.info("Api endpoint triggered")
    try:
        file_path = os.path.join('uploads', file_name)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return 'File not found', 404
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return 'An error occurred', 500

@google_drive_api.route('/delete/<file_name>', methods=['GET'])
def delete_uploaded_file( file_name):

    request_api_key = request.headers.get('shrek_key')

    if not is_valid_api_key(request_api_key):
        return jsonify({"message" : " Unauthorized : API key is incorrect"}), 401

    logging.info("Api endpoint triggered")
    try:
        file_path = os.path.join('uploads', file_name)
        if os.path.exists(file_path):
            os.remove(file_path)
            return 'File deleted successfully', 200
        else:
            return 'File not found', 404
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return 'An error occurred', 500