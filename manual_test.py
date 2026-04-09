import requests
import json
import logging

logging.basicConfig(level=logging.INFO)

url = "http://127.0.0.1:8000/extract"
file_path = "Jeweller_Invoice_Format.webp"

print(f"Testing API at {url} with file {file_path}...\n")

try:
    with open(file_path, "rb") as image_file:
        files = {"file": (file_path, image_file, "image/webp")}
        
        print("Sending POST request to /extract endpoint...")
        response = requests.post(url, files=files)
        
        print(f"\nStatus Code: {response.status_code}")
        
        try:
            # Try parsing as JSON
            response_data = response.json()
            print("\nResponse Data:")
            print(json.dumps(response_data, indent=2))
        except json.JSONDecodeError:
            # Fallback to raw text if not JSON
            print("\nRaw Response:")
            print(response.text)
            
except FileNotFoundError:
    print(f"Error: Could not find the file '{file_path}'")
except requests.exceptions.ConnectionError:
    print(f"Error: Could not connect to {url}. Make sure the FastAPI server is running!")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
