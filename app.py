from flask import Flask, render_template
import random
import os
import zipfile
from io import BytesIO
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseUpload
from dotenv import load_dotenv

app = Flask(__name__)

# Google Drive API settings
SCOPES = ['https://www.googleapis.com/auth/drive.file']
PARENT_FOLDER_ID = '197oZsCm4fZ0obRLmMiPKlqS7jwWwUIw-'  # Replace with your folder ID

# Load environment variables from .env file
load_dotenv()

# Construct the service account dictionary
SERVICE_ACCOUNT_INFO = {
    "type": "service_account",
    "project_id": os.getenv("GOOGLE_PROJECT_ID"),
    "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("GOOGLE_PRIVATE_KEY").replace(r'\\n', '\n'),
    "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
    "auth_uri": os.getenv("GOOGLE_AUTH_URI"),
    "token_uri": os.getenv("GOOGLE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("GOOGLE_AUTH_CERT_URL"),
    "client_x509_cert_url": os.getenv("GOOGLE_CLIENT_CERT_URL"),
    "universe_domain": os.getenv("GOOGLE_UNIVERSE_DOMAIN"),
}

def authenticate():
    """Authenticate with Google using the Service Account credentials."""
    try:
        credentials = service_account.Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
        print("✅ Authentication successful!")
        return credentials
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return None

def upload_zip(zip_bytes, file_name):
    """Uploads in-memory ZIP bytes to Google Drive and returns the public URL."""
    creds = authenticate()
    if not creds:
        return None
    
    try:
        service = build('drive', 'v3', credentials=creds)
        
        # Create file metadata
        file_metadata = {
            'name': file_name,
            'parents': [PARENT_FOLDER_ID]
        }
        
        # Create media upload object from bytes
        media = MediaIoBaseUpload(
            BytesIO(zip_bytes),
            mimetype='application/zip',
            resumable=True
        )
        
        # Upload file
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        file_id = file.get('id')
        
        # Make file public
        service.permissions().create(
            fileId=file_id,
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()
        
        # Generate public URL
        return f"https://drive.google.com/uc?id={file_id}"
    
    except Exception as e:
        print(f"🚨 Upload failed: {e}")
        return None

@app.route("/")
def index():
    """Render the main page with the download button."""
    return render_template("index.html", download_link=None)

@app.route("/generate")
def generate():
    """Generate a ZIP file in memory and upload it to Google Drive."""
    # Generate 1,000,000 random numbers
    text_content = "\n".join(str(random.randint(1, 1000)) for _ in range(1000000))
    
    # Create ZIP file in memory
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr('numbers.txt', text_content)
    
    # Get ZIP bytes
    zip_buffer.seek(0)
    zip_bytes = zip_buffer.getvalue()
    
    # Upload to Google Drive
    download_link = upload_zip(zip_bytes, 'random_numbers.zip')
    
    if download_link:
        return render_template("index.html", download_link=download_link)
    else:
        return "Failed to generate ZIP file", 500

if __name__ == "__main__":
    app.run(debug=True)