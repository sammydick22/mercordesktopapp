"""
Multi-threaded database test script to verify thread-safe operations
"""

import threading
import time
from services.database import DatabaseService

def test_client_crud(thread_id):
    """Test client CRUD operations in a separate thread"""
    print(f"Thread {thread_id}: Starting client CRUD test")
    # Each thread gets its own database connection
    db = DatabaseService()
    
    # Create a client
    client = db.create_client(
        name=f"Thread {thread_id} Client",
        user_id="test-user-123",
        contact_name=f"Contact Person {thread_id}",
        email=f"thread{thread_id}@example.com",
        phone=f"555-000-{thread_id}",
        notes=f"Created by thread {thread_id}"
    )
    
    if client and 'id' in client:
        client_id = client['id']
        print(f"Thread {thread_id}: Created client {client_id}")
        
        # Update the client
        updated = db.update_client(client_id, {"name": f"Updated Thread {thread_id} Client"})
        if updated:
            print(f"Thread {thread_id}: Updated client {client_id}")
        else:
            print(f"Thread {thread_id}: Failed to update client {client_id}")
        
        # Delete the client
        deleted = db.delete_client(client_id)
        if deleted:
            print(f"Thread {thread_id}: Deleted client {client_id}")
        else:
            print(f"Thread {thread_id}: Failed to delete client {client_id}")
    else:
        print(f"Thread {thread_id}: Failed to create client")

def test_time_entries(thread_id):
    """Test time entry operations in a separate thread"""
    print(f"Thread {thread_id}: Starting time entry test")
    # Each thread gets its own database connection
    db = DatabaseService()
    
    # Create a time entry
    time_entry = db.create_time_entry(
        user_id=f"test-user-{thread_id}",
        description=f"Test time entry from thread {thread_id}"
    )
    
    if time_entry and 'id' in time_entry:
        time_entry_id = time_entry['id']
        print(f"Thread {thread_id}: Created time entry {time_entry_id}")
        
        # Let it run for a moment
        time.sleep(1)
        
        # End the time entry
        ended = db.end_time_entry(time_entry_id)
        if ended:
            print(f"Thread {thread_id}: Ended time entry {time_entry_id}, duration: {ended.get('duration')}s")
        else:
            print(f"Thread {thread_id}: Failed to end time entry {time_entry_id}")
    else:
        print(f"Thread {thread_id}: Failed to create time entry")

def run_test():
    """Run multiple threads to test database thread safety"""
    threads = []
    
    # Create 5 threads running client CRUD operations
    for i in range(3):
        t = threading.Thread(target=test_client_crud, args=(i,))
        threads.append(t)
        
    # Create 5 threads running time entry operations
    for i in range(3, 6):
        t = threading.Thread(target=test_time_entries, args=(i,))
        threads.append(t)
    
    # Start all threads
    print("Starting all threads...")
    for t in threads:
        t.start()
    
    # Wait for all threads to complete
    for t in threads:
        t.join()
    
    print("All threads completed!")

if __name__ == "__main__":
    print("=== Testing Database Thread Safety ===")
    run_test()
    print("=== Test Completed ===")
