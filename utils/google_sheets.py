import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

# Configuration
# 👉 Ensure your Google Sheet is named exactly "Invoice Data"
SHEET_NAME = "Invoice Data"
CREDENTIALS_FILE = "credentials.json"

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

def save_to_sheet(data):
    """
    Appends extracted invoice data to a Google Sheet using oauth2client.
    """
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"ERROR: {CREDENTIALS_FILE} not found!")
        return False

    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
        client = gspread.authorize(creds)
        
        # Open by ID (more reliable than name)
        sheet = client.open_by_key("1eHFLuVtFvN_tKi101uETfqSthMQanENhWKIHOmNU2gY").sheet1

        row = [
            data.get("vendor_name", "Not found"),
            data.get("invoice_number", "Not found"),
            data.get("date", "Not found"),
            data.get("total_amount", "Not found")
        ]

        sheet.append_row(row)
        print("SUCCESS: Data saved to Google Sheets!")
        return True

    except Exception as e:
        print(f"FAILED: Google Sheets Error: {e}")
        return False
