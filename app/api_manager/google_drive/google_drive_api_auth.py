import os
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import logging



def Get_drive_service():
    # Define the scopes required by your application
    SCOPES = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/drive.file'
    ]

    # Load service account credentials from environment variables
    credentials = service_account.Credentials.from_service_account_info({
        "type": os.environ.get("google_drive_api_type"),
        "project_id": os.environ.get("google_adrive_api_project_id"),
        "private_key_id": os.environ.get("google_drive_api_private_key_id"),
        "private_key": os.environ.get("google_drive_api_private_key").replace('\\n', '\n'),
        "client_email": os.environ.get("google_drive_api_client_email"),
        "client_id": os.environ.get("google_drive_api_client_id"),
        "auth_uri": os.environ.get("google_drive_api_auth_uri"),
        "token_uri": os.environ.get("google_drive_api_token_uri"),
        "auth_provider_x509_cert_url": os.environ.get("google_drive_api_auth_provider_x509_cert_url"),
        "client_x509_cert_url": os.environ.get("google_drive_api_client_x509_cert_url"),
        "scopes": SCOPES
    })

    # Authenticate and create the Drive API service
    drive_service = build('drive', 'v3', credentials=credentials)
    logging.info("Succesfully retuned drive servive")
    if not drive_service:
        #TODO handle the exception
        logging.error(" -----   COULD NOT AUTHENTICATE ----")
    return drive_service