"""
Demonstration script to prove our database connection fix works.
"""
import os
import time
import threading
import uuid
from datetime import datetime
from services.database import DatabaseService

def create_client(db, thread_id):
    """Create a client in a thread"""
    print(f"Thread {thread_id}: Creating client...")
    
    client = db.create_client(
        name=f"Thread Client {thread_id}",
        user_id="test-user-123",
        contact_name=f"Contact Person {thread_id}",
        email=f"thread{thread_id}@example.com"
    )
    
    if client:
        print(f"Thread {thread_id}: SUCCESS - Client created with ID {client.get('id')}")
        print(f"Thread {thread_id}: Contact name: {client.get('contact_name')}")
    else:
        print(f"Thread {thread_id}: FAILED - Could not create client")

def run_test():
    """Run the test with multiple threads"""
    print("\n=== TESTING THREAD-SAFE DATABASE ACCESS ===\n")
    
    # Create shared database service
    db = DatabaseService()
    
    # Create and start threads
    threads = []
    for i in range(3):
        t = threading.Thread(target=create_client, args=(db, i))
        threads.append(t)
        t.start()
    
    # Wait for all threads to complete
    for t in threads:
        t.join()
    
    print("\n=== TEST COMPLETED ===\n")

if __name__ == "__main__":
    run_test()
