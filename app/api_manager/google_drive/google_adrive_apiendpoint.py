from flask import Blueprint, jsonify, request, send_file
import requests
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from io import BytesIO
from .google_drive_api_auth import Get_drive_service
import logging
import random
import string


google_drive_api = Blueprint('google_drive_api', __name__)


# Function to generate a random string
def generate_random_string(length):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for i in range(length))

@google_drive_api.route('/list_files')
def list_files():
    logging.info("Api endpoint triggered")

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



@google_drive_api.route('/get_file', methods=['GET'])
def get_file():
    logging.info("Get file API endpoint triggered")
    
    try:

        logging.info("entered try branch")
        file_id = request.args.get('file_id')  # Get the file ID from the request parameters
        logging.info("Cant get file id from URL")
        if not file_id:
            return jsonify({'error': 'File ID is required'}), 400

        # Get authenticated Drive API service
        drive_service = Get_drive_service()

        logging.info("Successfully authenticated with Google Drive API in get file endpoint")

        # Call Drive API to get file metadata
        file_metadata = drive_service.files().get(fileId=file_id).execute()

        # Download the file
        request = drive_service.files().get_media(fileId=file_id)
        file_bytes = BytesIO()
        downloader = MediaIoBaseDownload(file_bytes, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()

        # Set content type based on file type
        content_type = file_metadata['mimeType']

        # Return the file as a response
        file_bytes.seek(0)
        return send_file(file_bytes, mimetype=content_type, as_attachment=True, attachment_filename=file_metadata['name'])
    
    except Exception as e:
        error_details = getattr(e, 'resp', {}).get('error', {})
        error_reason = error_details.get('message', 'Unknown error')
        if isinstance(e, requests.exceptions.HTTPError) and e.response.status_code == 404:
            logging.error("File not found: {}".format(error_reason))
            return jsonify({'error': 'File not found'}), 404
        else:
            logging.error("Error occurred while retrieving file: {}".format(error_reason))
            if hasattr(e, 'response') and hasattr(e.response, 'json'):
                logging.error("Google Drive Response: {}".format(e.response.json()))
            else:
                logging.error("Google Drive Response: No response available")
            return jsonify({'error': 'Error occurred while retrieving file'}), 500

@google_drive_api.route('/create_file', methods=['POST'])
def create_file():
    logging.info("Create file API endpoint triggered")
    
    try:
        # Generate random content for the file
        content = generate_random_string(10)  # Adjust the length as needed

        # Get authenticated Drive API service
        drive_service = Get_drive_service()

        logging.info("Successfully authenticated with Google Drive API in create file endpoint")

        # Create file metadata
        file_metadata = {
            'name': 'random_file.txt',  # File name
            'parents': ['your_folder_id'],  # Folder ID where you want to place the file
            'description': 'Random file generated via API',  # Description of the file (optional)
            # Add more metadata fields as needed
        }

        # Upload the file with content and metadata
        media_body = MediaIoBaseUpload(BytesIO(content.encode()), mimetype='text/plain', resumable=True)
        new_file = drive_service.files().create(body=file_metadata, media_body=media_body).execute()

        logging.info("File created successfully with ID: {}".format(new_file['id']))

        return jsonify({'message': 'File created successfully', 'file_id': new_file['id']}), 200
    
    except Exception as e:
        logging.error("Error occurred while creating file: {}".format(str(e)))
        return jsonify({'error': 'Error occurred while creating file'}), 500