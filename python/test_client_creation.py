"""
Test script for client creation with contact_name parameter.
"""

from services.database import DatabaseService
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_client_creation():
    """Test client creation with contact_name parameter."""
    try:
        db = DatabaseService()
        
        # Create client with contact_name
        client_data = {
            "name": "Test Company",
            "user_id": "test-user-123",
            "contact_name": "John Doe",
            "email": "john@example.com",
            "phone": "555-123-4567"
        }
        
        logger.info(f"Creating client with data: {client_data}")
        
        # Extract name and user_id, pass the rest as kwargs
        name = client_data.pop("name")
        user_id = client_data.pop("user_id")
        
        # Create client
        new_client = db.create_client(name, user_id, **client_data)
        
        if new_client:
            logger.info(f"Successfully created client: {new_client}")
            return True
        else:
            logger.error("Failed to create client")
            return False
            
    except Exception as e:
        logger.error(f"Error creating client: {str(e)}")
        return False

if __name__ == "__main__":
    print("Starting client creation test...")
    success = test_client_creation()
    print(f"Test {'succeeded' if success else 'failed'}")
    
    # Try direct connection for comparison
    import sqlite3
    from datetime import datetime
    import uuid
    import os
    from utils.config import Config
    
    print("\nTrying direct database access for comparison:")
    try:
        config = Config()
        db_dir = config.get("storage.database_dir")
        if not db_dir:
            db_dir = os.path.join(config.get_app_dir(), "db")
        db_path = os.path.join(db_dir, "timetracker.db")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        client_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        name = "Direct Test Company"
        user_id = "test-user-456"
        contact_name = "Jane Smith"
        
        print(f"Inserting client directly with contact_name: {contact_name}")
        
        cursor.execute(
            '''
            INSERT INTO clients
            (id, name, contact_name, email, phone, address, notes, 
            is_active, created_at, updated_at, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                client_id,
                name,
                contact_name,
                "jane@example.com",
                "555-987-6543",
                None,
                None,
                1,
                now,
                now,
                user_id
            )
        )
        
        conn.commit()
        
        # Check if client was created
        cursor.execute("SELECT id, name, contact_name FROM clients WHERE id = ?", (client_id,))
        result = cursor.fetchone()
        if result:
            print(f"Direct client creation succeeded: {result}")
        else:
            print("Direct client creation failed: No client found")
            
        conn.close()
    except Exception as e:
        print(f"Direct client creation error: {str(e)}")
