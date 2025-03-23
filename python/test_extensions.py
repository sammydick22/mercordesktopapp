"""
Test script to verify that the database and sync extensions are working.
"""
import asyncio
import logging
import uuid
from services.database import DatabaseService
from services.sync import SyncService
from utils.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_database_extensions():
    """Test that the database extensions are working."""
    print("\n==== Testing Database Extensions ====\n")
    
    # Initialize database service
    config = Config()
    db = DatabaseService(config)
    
    # Test client methods
    print("Testing client methods...")
    user_id = "test-user-1"
    client_name = "Test Client"
    
    # Create client
    client = db.create_client(client_name, user_id, contact_name="Contact Person")
    client_id = client.get("id")
    
    if client and client.get("name") == client_name:
        print(f"✅ Created client: {client_name} with ID: {client_id}")
    else:
        print("❌ Failed to create client")
        return False
    
    # Get client
    retrieved_client = db.get_client(client_id)
    if retrieved_client and retrieved_client.get("id") == client_id:
        print(f"✅ Retrieved client: {retrieved_client.get('name')}")
    else:
        print("❌ Failed to retrieve client")
        return False
    
    # Update client
    updated_client = db.update_client(client_id, contact_name="New Contact")
    if updated_client and updated_client.get("contact_name") == "New Contact":
        print(f"✅ Updated client: {updated_client.get('name')}")
    else:
        print("❌ Failed to update client")
        return False
    
    # Get all clients
    clients = db.get_clients(user_id=user_id)
    if clients and len(clients) > 0:
        print(f"✅ Retrieved {len(clients)} clients")
    else:
        print("❌ Failed to retrieve clients")
        return False
    
    # Test project methods
    print("\nTesting project methods...")
    project_name = "Test Project"
    
    # Create project
    project = db.create_project(project_name, user_id, client_id=client_id, description="Test project description")
    project_id = project.get("id")
    
    if project and project.get("name") == project_name:
        print(f"✅ Created project: {project_name} with ID: {project_id}")
    else:
        print("❌ Failed to create project")
        return False
    
    # Get project
    retrieved_project = db.get_project(project_id)
    if retrieved_project and retrieved_project.get("id") == project_id:
        print(f"✅ Retrieved project: {retrieved_project.get('name')}")
    else:
        print("❌ Failed to retrieve project")
        return False
    
    # Test task methods
    print("\nTesting task methods...")
    task_name = "Test Task"
    
    # Create task
    task = db.create_project_task(task_name, project_id, description="Test task description")
    task_id = task.get("id")
    
    if task and task.get("name") == task_name:
        print(f"✅ Created task: {task_name} with ID: {task_id}")
    else:
        print("❌ Failed to create task")
        return False
    
    # Get task
    retrieved_task = db.get_project_task(task_id)
    if retrieved_task and retrieved_task.get("id") == task_id:
        print(f"✅ Retrieved task: {retrieved_task.get('name')}")
    else:
        print("❌ Failed to retrieve task")
        return False
    
    # Get project tasks
    tasks = db.get_project_tasks(project_id)
    if tasks and len(tasks) > 0:
        print(f"✅ Retrieved {len(tasks)} tasks for project {project_id}")
    else:
        print("❌ Failed to retrieve tasks")
        return False
    
    # Test user settings methods
    print("\nTesting user settings methods...")
    
    # Get settings (should create default settings)
    settings = db.get_user_settings(user_id)
    if settings and settings.get("user_id") == user_id:
        print(f"✅ Retrieved user settings for user {user_id}")
    else:
        print("❌ Failed to retrieve user settings")
        return False
    
    # Update settings
    updated_settings = db.update_user_settings(
        user_id, 
        screenshot_interval=300, 
        theme="dark"
    )
    if (updated_settings and 
        updated_settings.get("screenshot_interval") == 300 and 
        updated_settings.get("theme") == "dark"):
        print(f"✅ Updated user settings")
    else:
        print("❌ Failed to update user settings")
        return False
    
    # Test user profile methods
    print("\nTesting user profile methods...")
    
    # Get profile (should create default profile)
    profile = db.get_user_profile(user_id)
    if profile and profile.get("user_id") == user_id:
        print(f"✅ Retrieved user profile for user {user_id}")
    else:
        print("❌ Failed to retrieve user profile")
        return False
    
    # Update profile
    updated_profile = db.update_user_profile(
        user_id, 
        name="Test User", 
        email="test@example.com"
    )
    if (updated_profile and 
        updated_profile.get("name") == "Test User" and 
        updated_profile.get("email") == "test@example.com"):
        print(f"✅ Updated user profile")
    else:
        print("❌ Failed to update user profile")
        return False
    
    # Clean up (optional)
    # Delete task
    if db.delete_project_task(task_id):
        print(f"✅ Deleted task {task_id}")
    else:
        print(f"❌ Failed to delete task {task_id}")
    
    # Delete project
    if db.delete_project(project_id):
        print(f"✅ Deleted project {project_id}")
    else:
        print(f"❌ Failed to delete project {project_id}")
    
    # Delete client
    if db.delete_client(client_id):
        print(f"✅ Deleted client {client_id}")
    else:
        print(f"❌ Failed to delete client {client_id}")
    
    print("\nDatabase extensions test completed successfully!")
    return True

async def test_sync_service_extensions():
    """Test that the sync service extensions are working."""
    print("\n==== Testing Sync Service Extensions ====\n")
    
    # Initialize services
    config = Config()
    db = DatabaseService(config)
    sync = SyncService(config, db)
    
    # Check if sync extensions methods exist
    has_client_sync = hasattr(sync, "_sync_clients")
    has_project_sync = hasattr(sync, "_sync_projects")
    has_task_sync = hasattr(sync, "_sync_project_tasks")
    has_settings_sync = hasattr(sync, "_sync_user_settings")
    has_profile_sync = hasattr(sync, "_sync_user_profile")
    
    if all([has_client_sync, has_project_sync, has_task_sync, has_settings_sync, has_profile_sync]):
        print("✅ All sync extension methods exist")
    else:
        print("❌ Some sync extension methods are missing:")
        if not has_client_sync: print("  - _sync_clients")
        if not has_project_sync: print("  - _sync_projects")
        if not has_task_sync: print("  - _sync_project_tasks")
        if not has_settings_sync: print("  - _sync_user_settings")
        if not has_profile_sync: print("  - _sync_user_profile")
        return False
    
    # Check if original sync_all method was preserved
    if hasattr(sync, "_original_sync_all"):
        print("✅ Original sync_all method preserved")
    else:
        print("❌ Original sync_all method not preserved")
        return False
    
    # Check if original get_sync_status method was preserved
    if hasattr(sync, "_original_get_sync_status"):
        print("✅ Original get_sync_status method preserved")
    else:
        print("❌ Original get_sync_status method not preserved")
        return False
    
    # Get sync status
    status = sync.get_sync_status()
    
    # Check if extended status includes new entities
    if "unsynced_counts" in status:
        unsynced = status["unsynced_counts"]
        if all(entity in unsynced for entity in ["clients", "projects", "project_tasks"]):
            print("✅ Extended sync status includes new entities")
        else:
            print("❌ Extended sync status missing some entities")
            return False
    
    print("\nSync service extensions test completed successfully!")
    return True

async def main():
    try:
        # Test database extensions
        db_success = await test_database_extensions()
        
        # Test sync service extensions
        sync_success = await test_sync_service_extensions()
        
        if db_success and sync_success:
            print("\n✅ All extension tests passed successfully!")
        else:
            print("\n❌ Some extension tests failed.")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        print(f"\nTest failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
