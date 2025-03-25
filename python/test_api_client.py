"""
Test the FastAPI client creation endpoint
"""
import json
import requests
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_create_client():
    """Test creating a client through the API endpoint"""
    # Define API endpoint
    url = "http://localhost:8000/clients/"
    
    # Define client data with contact_name
    client_data = {
        "name": "API Test Client",
        "contact_name": "John Contact",
        "email": "api-test@example.com",
        "phone": "555-API-TEST",
        "notes": "Created via API test script"
    }
    
    # Set mock auth headers (since the API requires authentication)
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer test-token"  # This is mocked since we're testing locally
    }
    
    logger.info(f"Sending POST request to {url} with data: {client_data}")
    
    try:
        # Make POST request
        response = requests.post(url, json=client_data, headers=headers)
        
        # Check response
        if response.status_code == 200 or response.status_code == 201:
            logger.info(f"Success! Status code: {response.status_code}")
            logger.info(f"Response: {response.json()}")
            return True
        else:
            logger.error(f"Error! Status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Exception occurred: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing client creation API endpoint...")
    success = test_create_client()
    print(f"Test {'succeeded' if success else 'failed'}")
