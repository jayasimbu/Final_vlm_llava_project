import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.google_sheets import save_to_sheet

logger = logging.getLogger(__name__)


def test_connection() -> bool:
    """Test Google Sheets connection with dummy data."""
    dummy_data = {
        "vendor_name": "CONNECTION_TEST",
        "invoice_number": "000",
        "date": "2026-01-01",
        "total_amount": "0.00",
    }
    return save_to_sheet(dummy_data)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = test_connection()
    if success:
        logger.info("Google Sheets connection successful")
    else:
        logger.error("Google Sheets connection failed")
