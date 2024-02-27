import os
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import logging



def Get_drive_service():
    # Load service account credentials from environment variables
    credentials = service_account.Credentials.from_service_account_info({
        "type": os.environ.get("GOOGLE_DRIVE_API_TYPE"),
        "project_id": os.environ.get("GOOGLE_ADRIVE_API_PROJECT_ID"),
        "private_key_id": os.environ.get("GOOGLE_DRIVE_API_PRIVATE_KEY_ID"),
        "private_key": os.environ.get("GOOGLE_DRIVE_API_PRIVATE_KEY").replace('\\n', '\n'),
        "client_email": os.environ.get("GOOGLE_DRIVE_API_CLIENT_EMAIL"),
        "client_id": os.environ.get("GOOGLE_DRIVE_API_CLIENT_ID"),
        "auth_uri": os.environ.get("GOOGLE_DRIVE_API_AUTH_URI"),
        "token_uri": os.environ.get("GOOGLE_DRIVE_API_TOKEN_URI"),
        "auth_provider_x509_cert_url": os.environ.get("GOOGLE_DRIVE_API_AUTH_PROVIDER_X509_CERT_URL"),
        "client_x509_cert_url": os.environ.get("GOOGLE_DRIVE_API_CLIENT_X509_CERT_URL")
    })



    # Authenticate and create the Drive API service
    drive_service = build('drive', 'v3', credentials=credentials)
    logging.info("Succesfully retuned drive servive")
    return drive_service

# Now you can use drive_service to interact with Google Drive API
