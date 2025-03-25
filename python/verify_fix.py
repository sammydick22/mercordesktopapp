"""
Simple verification script for the database fix
"""

from services.database import DatabaseService

if __name__ == "__main__":
    print("=== Testing Contact Name Fix ===")
    
    # Create database service
    db = DatabaseService()
    
    # Create a client with contact_name
    print("Creating client with contact_name...")
    
    try:
        client = db.create_client(
            name="Fix Verification Client",
            user_id="test-user-fix",
            contact_name="Contact Test Person", 
            email="fix-test@example.com"
        )
        
        if client and 'id' in client:
            print("SUCCESS: Client created successfully!")
            print(f"Client ID: {client['id']}")
            print(f"Name: {client['name']}")
            print(f"Contact Name: {client['contact_name']}")
            print(f"Email: {client['email']}")
            print("The fix has been successfully applied.")
        else:
            print("ERROR: Client creation failed.")
            print("The fix may not be properly applied.")
    except Exception as e:
        print(f"ERROR: An exception occurred: {str(e)}")
        print("The fix may not be properly applied.")
