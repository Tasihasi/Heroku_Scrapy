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
    
    

@google_drive_api.route('/create_file', methods=['POST'])
def create_file(file_name : str, file_mimeType : str):
    # Assuming the file content is sent as part of the request body
    file_content = request.data.decode('utf-8')  # Decode the bytes to string assuming utf-8 encoding
    

    # Additional code to create the file in Google Drive or perform any other actions
    
    # Get authenticated Drive API service
    drive_service = Get_drive_service()

    file_metadata = {
        'name': file_name,
        'mimeType': file_mimeType
    }

    media = MediaIoBaseUpload(io.BytesIO(file_content.encode('utf-8')), mimetype='text/plain')


    

    logging.info("Create the file with the provided content")


    try:
        # Create the file with the provided content
        file = (
            drive_service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )

        # Adjust file permissions to allow the service account to read and alter it
        permission = {
            'type': 'anyone',
            'role': 'reader',
            #'emailAddress': 'YOUR_SERVICE_ACCOUNT_EMAIL_HERE'
        }

        drive_service.permissions().create(fileId=file['id'], body=permission).execute()

        # Return a response indicating success
        return "File created successfully", 200

    except Exception as e:
        # Handle any exceptions that occur during the upload process
        logging.error("An error occurred during file upload: %s", str(e))
        return "Error occurred during file upload", 500


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
    