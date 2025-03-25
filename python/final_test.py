"""
Final test script with better error handling
"""
import sys
import traceback
from services.database import DatabaseService

def main():
    try:
        print("Creating database service...")
        db = DatabaseService()
        print("Database service created successfully")
        
        print("\nAttempting to create client with contact_name...")
        client = db.create_client(
            name="Final Test Client",
            user_id="test-user-999",
            contact_name="Final Contact Person"
        )
        
        if client:
            print("\nSUCCESS: Client created with following details:")
            for key, value in client.items():
                print(f"  {key}: {value}")
            return True
        else:
            print("\nFAILED: Client was not created")
            return False
            
    except Exception as e:
        print("\nERROR: An exception occurred")
        print(f"Exception type: {type(e).__name__}")
        print(f"Exception message: {str(e)}")
        print("\nTraceback:")
        traceback.print_exc(file=sys.stdout)
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("FINAL TEST OF DATABASE FIX")
    print("=" * 50)
    
    result = main()
    
    print("\n" + "=" * 50)
    if result:
        print("TEST SUCCEEDED - The fix is working!")
    else:
        print("TEST FAILED - Further investigation needed")
    print("=" * 50)
