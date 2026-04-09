import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.google_sheets import save_to_sheet

def test_connection():
    print("\n--- GOOGLE SHEETS CONNECTION TEST ---")
    dummy_data = {
        "vendor_name": "CONNECTION_TEST",
        "invoice_number": "000",
        "date": "2026-01-01",
        "total_amount": "0.00"
    }
    
    success = save_to_sheet(dummy_data)
    
    if success:
        print("\nSUCCESS: Connection verified! Check your Google Sheet.")
    else:
        print("\nFAILED: Please ensure you 'Shared' the sheet with the email in credentials.json.")
    print("--------------------------------------\n")

if __name__ == "__main__":
    test_connection()
