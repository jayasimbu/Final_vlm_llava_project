import logging
import os

import gspread
from oauth2client.service_account import ServiceAccountCredentials

logger = logging.getLogger(__name__)

CREDENTIALS_FILE = "credentials.json"

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

def save_to_sheet(data: dict) -> bool:
    """Append extracted invoice data to configured Google Sheet.
    
    Requires credentials.json with valid Google service account credentials.
    
    Args:
        data: Dictionary with vendor_name, invoice_number, date, total_amount
        
    Returns:
        True if successful, False on error
    """
    if not os.path.exists(CREDENTIALS_FILE):
        logger.error(f"Credentials file not found: {CREDENTIALS_FILE}")
        return False

    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
        client = gspread.authorize(creds)
        
        sheet = client.open_by_key("1eHFLuVtFvN_tKi101uETfqSthMQanENhWKIHOmNU2gY").sheet1

        row = [
            data.get("vendor_name", "Not found"),
            data.get("invoice_number", "Not found"),
            data.get("date", "Not found"),
            data.get("total_amount", "Not found")
        ]

        sheet.append_row(row)
        logger.info("Data saved to Google Sheets")
        return True

    except Exception as e:
        logger.error(f"Google Sheets error: {e}")
        return False
