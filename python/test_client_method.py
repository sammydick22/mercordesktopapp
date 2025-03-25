"""
Test script to check the DatabaseService.create_client method.
"""
from services.database import DatabaseService
import logging
import sys

# Setup logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_create_client():
    db = DatabaseService()
    
    # Print the method signature to check parameters
    import inspect
    sig = inspect.signature(db.create_client)
    print(f"create_client signature: {sig}")
    
    # List all methods that include 'client' in their name
    methods = [method for method in dir(db) if 'client' in method]
    print(f"Available client methods: {methods}")
    
    # Check the source code of create_client
    try:
        print("Source code of create_client:")
        print(inspect.getsource(db.create_client))
    except Exception as e:
        print(f"Error getting source: {e}")
    
    # Test creating a client
    try:
        client = db.create_client(
            name="Test Client",
            user_id="test_user",
            contact_name="Test Contact",
            email="test@example.com"
        )
        print(f"Created client: {client}")
    except TypeError as e:
        print(f"TypeError: {e}")
        
if __name__ == "__main__":
    test_create_client()
