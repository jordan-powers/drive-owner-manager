from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive"]

script_dir = Path(__file__).parent

token_path = script_dir / 'token.json'
credentials_path = script_dir / 'credentials.json'

def get_creds():
    creds = None
    if token_path.is_file():
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server()
        with token_path.open('w') as token_file:
            token_file.write(creds.to_json())
    return creds
