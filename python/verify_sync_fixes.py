"""
Script to verify that the sync fixes for project_tasks and screenshots work correctly.
This script:
1. Resets the sync state for project_tasks and screenshots
2. Attempts to sync them
3. Verifies the results
"""
import os
import sys
import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our modules
from reset_sync_state import reset_sync_state
from services.database import DatabaseService
from services.supabase_auth import SupabaseAuthService
from services.supabase_sync import SupabaseSyncService

async def verify_sync_fixes():
    """Verify that the sync fixes for project_tasks and screenshots work correctly."""
    print("\n" + "="*40)
    print("TESTING SYNC FIXES FOR PROJECT TASKS AND SCREENSHOTS")
    print("="*40 + "\n")
    
    # Step 1: Reset sync state to force a fresh sync
    print("\n[Step 1] Resetting sync state for project_tasks and screenshots...")
    reset_result = reset_sync_state(['project_tasks', 'screenshots'])
    if not reset_result:
        print("⚠️ Could not reset sync state, but continuing anyway.")
    
    # Step 2: Initialize services
    print("\n[Step 2] Initializing database and auth services...")
    db_service = DatabaseService()
    auth_service = SupabaseAuthService()
    
    # Step 3: Check if user is authenticated
    print("\n[Step 3] Checking authentication status...")
    is_auth = await auth_service.is_authenticated_async()
    if not is_auth:
        print("❌ Not authenticated. Please run the app and login first.")
        return False
    
    user = await auth_service.get_user()
    print(f"✅ Authenticated as user: {user.get('email')}")
    
    # Step 4: Initialize sync service
    print("\n[Step 4] Initializing sync service...")
    sync_service = SupabaseSyncService(db_service, auth_service)
    init_result = await sync_service.initialize()
    if not init_result:
        print("❌ Failed to initialize sync service.")
        return False
    print("✅ Sync service initialized")
    
    # Step 5: Check for unsynchronized tasks
    print("\n[Step 5] Checking for unsynchronized project tasks...")
    tasks = db_service.get_unsynchronized_project_tasks()
    if not tasks:
        print("⚠️ No unsynchronized project tasks found. This is not an error, but it means we can't verify the project_tasks fix.")
    else:
        print(f"✅ Found {len(tasks)} unsynchronized project tasks")
    
    # Step 6: Check for unsynchronized screenshots
    print("\n[Step 6] Checking for unsynchronized screenshots...")
    screenshots = db_service.get_unsynchronized_screenshots(0)  # Use 0 to check all
    if not screenshots:
        print("⚠️ No unsynchronized screenshots found. This is not an error, but it means we can't verify the screenshots fix.")
    else:
        print(f"✅ Found {len(screenshots)} unsynchronized screenshots")
        # Print some screenshot info for debugging
        if len(screenshots) > 0:
            sample = screenshots[0]
            print(f"   Sample screenshot ID: {sample['id']}")
            print(f"   UUID format: {is_valid_uuid(sample['id'])}")
    
    # Step 7: Test project tasks sync
    print("\n[Step 7] Testing project tasks sync...")
    if tasks:
        task_result = await sync_service.sync_tasks()
        if task_result.get("status") == "complete" or task_result.get("status") == "partial":
            if task_result.get("synced", 0) > 0:
                print(f"✅ Successfully synced {task_result.get('synced')} project tasks to Supabase")
            else:
                print("⚠️ No project tasks were synced. This might indicate a problem.")
        else:
            print(f"❌ Project tasks sync failed with status: {task_result.get('status')}")
    else:
        print("⏩ Skipping project tasks sync test due to no unsynchronized tasks")
    
    # Step 8: Test screenshots sync
    print("\n[Step 8] Testing screenshots sync...")
    if screenshots:
        screenshot_result = await sync_service.sync_screenshots()
        if screenshot_result.get("status") == "complete" or screenshot_result.get("status") == "partial":
            if screenshot_result.get("synced", 0) > 0:
                print(f"✅ Successfully synced {screenshot_result.get('synced')} screenshots to Supabase")
            else:
                print("⚠️ No screenshots were synced. This might indicate a problem.")
        else:
            print(f"❌ Screenshots sync failed with status: {screenshot_result.get('status')}")
    else:
        print("⏩ Skipping screenshots sync test due to no unsynchronized screenshots")
    
    # Summary
    print("\n" + "="*40)
    print("VERIFICATION SUMMARY")
    print("="*40)
    
    if not tasks and not screenshots:
        print("\n⚠️ No unsynchronized data was found to test with.")
        print("   To fully test the fixes, please:")
        print("   1. Run the app")
        print("   2. Create at least one project task")
        print("   3. Capture at least one screenshot")
        print("   4. Run this verification script again")
    else:
        print("\n✅ The verification script has completed.")
        if tasks and task_result.get("synced", 0) > 0:
            print("✅ Project tasks sync is now FIXED!")
        
        if screenshots and screenshot_result.get("synced", 0) > 0:
            print("✅ Screenshots sync is now FIXED!")
    
    print("\nTo verify these fixes in the app:")
    print("1. Run the application")
    print("2. Create a new project and task")
    print("3. Start a time entry with the task")
    print("4. Take screenshots")
    print("5. Use the sync button to sync data")
    print("6. Check the sync logs - there should be no errors for project tasks or screenshots")
    
    return True

def is_valid_uuid(uuid_str):
    """Check if a string is a valid UUID."""
    import uuid
    try:
        uuid_obj = uuid.UUID(uuid_str)
        return True
    except (ValueError, AttributeError, TypeError):
        return False

if __name__ == "__main__":
    asyncio.run(verify_sync_fixes())
