from flask import Blueprint, jsonify
from google_drive_api_auth import Get_drive_service
import logging


google_drive_api = Blueprint('google_drive_api', __name__)

@google_drive_api.route('/list_files')
def list_files():
    logging.INFO("Api endpoint triggered")
    # Get authenticated Drive API service
    drive_service = Get_drive_service()

    # Call Drive API to list files
    results = drive_service.files().list(pageSize=10).execute()
    logging.INFO("Succesfully autharized")

    items = results.get('files', [])

    if not items:
        return jsonify({'message': 'No files found'})
    else:
        # Extract file names
        file_names = [item['name'] for item in items]
        return jsonify({'files': file_names})