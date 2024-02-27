from flask import Blueprint, jsonify, request, send_file
from googleapiclient.http import MediaIoBaseDownload
from io import BytesIO
from .google_drive_api_auth import Get_drive_service
import logging


google_drive_api = Blueprint('google_drive_api', __name__)

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
            file_names = [item['name'] for item in items]
            return jsonify({'files': file_names})
    
    except Exception as e:
        logging.error("Authentication failed or an error occurred: {}".format(str(e)))
        return jsonify({'error': 'Authentication failed or an error occurred'}), 500



@google_drive_api.route('/get_file', methods=['GET'])
def get_file():
    logging.info("API endpoint triggered")
    
    try:
        file_id = request.args.get('file_id')  # Get the file ID from the request parameters
        if not file_id:
            return jsonify({'error': 'File ID is required'}), 400

        # Get authenticated Drive API service
        drive_service = Get_drive_service()

        logging.info("Successfully authenticated with Google Drive API")

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
        error_details = e.resp.get('error', {})
        error_reason = error_details.get('message', 'Unknown error')
        if e.resp.status == 404:
            return jsonify({'error': 'File not found'}), 404
        else:
            logging.error("Error occurred while retrieving file: {}".format(error_reason))
            return jsonify({'error': 'Error occurred while retrieving file'}), 500
