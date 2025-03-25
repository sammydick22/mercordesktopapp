"""
Simple test for client creation
"""
from services.database import DatabaseService
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        print("Creating database service...")
        db = DatabaseService()
        
        print("Creating client with contact_name...")
        client = db.create_client(
            name="Test Client",
            user_id="test-user-123",
            contact_name="Contact Person",
            email="test@example.com"
        )
        
        if client:
            print(f"SUCCESS: Client created: {client}")
        else:
            print("FAILED: Client not created")
    except Exception as e:
        print(f"ERROR: {e}")
