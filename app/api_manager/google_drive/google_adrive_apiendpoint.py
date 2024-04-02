from flask import Blueprint, jsonify, send_file
from flask import request
import requests
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from io import BytesIO
import io
from .google_drive_api_auth import Get_drive_service
import logging
import random
import string
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import json

from google_drive_actions import upload_basic



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



@google_drive_api.route('/get_file/<file_id>', methods=['GET'])
def get_file(file_id):


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

        # You can now use the file_content object to do whatever you want with the file content

        # For example, you can return the file content as a response
        return send_file(file_content, mimetype=file_metadata['mimeType'], as_attachment=True, download_name=file_metadata['name'])
        
    except Exception as e:
        # Handle any errors that occur during the process
        print("An error occurred:", e)
        return "Error occurred while retrieving the file.", 500
    
    

@google_drive_api.route('/create_file', methods=['GET' , 'POST'])
def create_file():
    

    return upload_basic("something", "test.txt")

    

@google_drive_api.route('/delete_file/<file_id>', methods=['GET'])
def delete_file(file_id):
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
    