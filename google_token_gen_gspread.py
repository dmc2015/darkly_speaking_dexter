import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Define the scope for Google Drive API
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

# Provide the path to your JSON key file
credentials = ServiceAccountCredentials.from_json_keyfile_name('data/darklyspeakingdexter-c637f22f8d1c.json', scope)

# Authorize gspread with the credentials
gc = gspread.authorize(credentials)

# Example: List files in Google Drive (optional, for testing purposes)
from googleapiclient.discovery import build
drive_service = build('drive', 'v3', credentials=credentials)

results = drive_service.files().list(pageSize=10).execute()
files = results.get('files', [])
for file in files:
    print(f"Found file: {file['name']} ({file['id']})")
