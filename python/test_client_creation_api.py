"""
Test script to verify the fix for client creation API.
"""
import requests
import json
import logging
import sys

# Setup logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_create_client():
    """Test creating a client through the API with contact_name included."""
    
    # API endpoint for client creation
    url = "http://127.0.0.1:8000/clients/"
    
    # In a real scenario, we would need authorization, but for this test
    # we'll assume the API is not checking auth or we have a valid token
    
    # Client data including contact_name
    client_data = {
        "name": "Test Client API",
        "contact_name": "Test Contact API",
        "email": "test_api@example.com",
        "phone": "123-456-7890",
        "address": "123 API Street",
        "notes": "This is a test client",
        "is_active": True
    }
    
    # Make the POST request
    try:
        headers = {"Content-Type": "application/json"} 
        
        # Assuming the API is running and we have authorization
        # In a real scenario we would add: 
        # headers["Authorization"] = f"Bearer {token}"
        
        response = requests.post(url, data=json.dumps(client_data), headers=headers)
        
        # Print response
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Success! Client created successfully with contact_name!")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {str(e)}")
        
if __name__ == "__main__":
    test_create_client()
