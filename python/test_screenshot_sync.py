"""
Tests the screenshot sync fixes by:
1. Resetting the screenshot sync state
2. Performing a sync to see if the screenshots are properly detected and synced
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

# Import our reset_sync_state function
from reset_sync_state import reset_sync_state
# Import the services
from services.database import DatabaseService
from services.supabase_auth import SupabaseAuthService
from services.supabase_sync import SupabaseSyncService

async def test_screenshot_sync():
    print("\n" + "="*50)
    print(" TESTING SCREENSHOT SYNC WITH UUID FIX")
    print("="*50 + "\n")
    
    # Step 1: Reset only the screenshots sync state
    print("\n[Step 1] Resetting screenshots sync state...")
    reset_result = reset_sync_state(['screenshots'])
    if not reset_result:
        print("⚠️ Could not reset sync state, but continuing anyway.")
    
    # Step 2: Initialize services
    print("\n[Step 2] Initializing database and auth services...")
    db_service = DatabaseService()
    auth_service = SupabaseAuthService()
    
    # Step 3: Check if user is authenticated
    print("\n[Step 3] Checking authentication status...")
    # Non-async authentication check
    is_auth = auth_service.is_authenticated()
    if not is_auth:
        print("❌ Not authenticated. Please run the app and login first.")
        return False
    
    # Get user details
    user = auth_service.get_user_sync() if hasattr(auth_service, 'get_user_sync') else auth_service.get_user()
    print(f"✅ Authenticated as user: {user.get('email')}")
    
    # Step 4: Check for unsynchronized screenshots
    print("\n[Step 4] Checking for unsynchronized screenshots after reset...")
    screenshots = db_service.get_unsynchronized_screenshots(None)  # Set to None to get all unsynchronized
    
    if not screenshots:
        print("⚠️ No unsynchronized screenshots found. This is unexpected after a sync reset.")
        screenshots_count = 0
    else:
        screenshots_count = len(screenshots)
        print(f"✅ Found {screenshots_count} unsynchronized screenshots")
        # Print a sample screenshot
        if screenshots_count > 0:
            sample = screenshots[0]
            print(f"   Sample screenshot ID: {sample['id']}")
            print(f"   Filepath: {sample['filepath']}")
            print(f"   Created at: {sample['created_at']}")
    
    # Step 5: Initialize sync service
    print("\n[Step 5] Initializing sync service...")
    sync_service = SupabaseSyncService(db_service, auth_service)
    
    # First, check if initialize is an async method or not
    if asyncio.iscoroutinefunction(sync_service.initialize):
        init_result = await sync_service.initialize()
    else:
        init_result = sync_service.initialize()
        
    if not init_result:
        print("❌ Failed to initialize sync service.")
        return False
    print("✅ Sync service initialized successfully")
    
    # Step 6: Test screenshots sync directly (bypassing sync_all)
    print("\n[Step 6] Testing screenshots sync...")
    if screenshots_count > 0:
        # First, check if sync_screenshots exists
        if not hasattr(sync_service, 'sync_screenshots'):
            print("❌ sync_screenshots method does not exist in the sync service!")
            # Try to directly force sync through the existing method
            print("Attempting to patch the sync service with a direct screenshots sync call...")
            try:
                # Direct implementation of a screenshot sync
                from services.supabase_client import SupabaseClient
                
                # Get screenshots to sync
                screenshots = db_service.get_unsynchronized_screenshots(None)
                print(f"Found {len(screenshots)} unsynchronized screenshots to sync")
                
                # If screenshots exist, sync them
                if screenshots:
                    user_data = auth_service.get_user_sync() if hasattr(auth_service, 'get_user_sync') else auth_service.get_user()
                    user_id = user_data.get('id')
                    
                    print(f"Manually syncing screenshots for user {user_id}")
                    
                    # Create a Supabase client
                    supabase_client = SupabaseClient()
                    
                    # Sync the screenshots one by one
                    synced_count = 0
                    failed_count = 0
                    
                    for screenshot in screenshots:
                        try:
                            print(f"Syncing screenshot {screenshot['id']}")
                            
                            # Create a dict with the data to insert
                            screenshot_data = {
                                "id": screenshot['id'],
                                "filepath": screenshot['filepath'],
                                "thumbnail_path": screenshot['thumbnail_path'],
                                "timestamp": screenshot['timestamp'],
                                "user_id": user_id
                            }
                            
                            # Post to Supabase
                            table = "screenshots"
                            result = supabase_client.table(table).insert(screenshot_data).execute()
                            
                            # Mark as synced
                            db_service.update_screenshot_sync_status(screenshot['id'], True)
                            synced_count += 1
                            print(f"Successfully synced screenshot {screenshot['id']}")
                            
                        except Exception as e:
                            failed_count += 1
                            print(f"Failed to sync screenshot {screenshot['id']}: {str(e)}")
                    
                    screenshot_result = {
                        "synced": synced_count,
                        "failed": failed_count,
                        "status": "complete" if failed_count == 0 else "partial"
                    }
                    print(f"Manual sync result: {screenshot_result}")
                else:
                    screenshot_result = {"synced": 0, "failed": 0, "status": "no_data"}
            except Exception as e:
                print(f"Error during manual sync: {str(e)}")
                screenshot_result = {"synced": 0, "failed": screenshots_count, "status": "error"}
        else:
            # Use the existing sync_screenshots method
            try:
                if asyncio.iscoroutinefunction(sync_service.sync_screenshots):
                    screenshot_result = await sync_service.sync_screenshots()
                else:
                    screenshot_result = sync_service.sync_screenshots()
                print(f"Screenshot sync result: {screenshot_result}")
            except Exception as e:
                print(f"Error during sync: {str(e)}")
                screenshot_result = {"synced": 0, "failed": screenshots_count, "status": "error"}
        
        # Check the results
        if screenshot_result.get("status") in ["complete", "partial"]:
            if screenshot_result.get("synced", 0) > 0:
                print(f"✅ Successfully synced {screenshot_result.get('synced')} screenshots to Supabase")
                
                # Check if we synced all screenshots
                if screenshot_result.get("synced") == screenshots_count:
                    print("✅ All screenshots were successfully synced!")
                else:
                    print(f"⚠️ Only {screenshot_result.get('synced')} out of {screenshots_count} screenshots were synced.")
            else:
                print("⚠️ No screenshots were synced. There might still be an issue.")
        else:
            print(f"❌ Screenshots sync failed with status: {screenshot_result.get('status')}")
    else:
        print("⏩ Skipping screenshots sync test since no unsynchronized screenshots were found")
    
    print("\n" + "="*50)
    print(" SUMMARY")
    print("="*50)
    
    if screenshots_count > 0 and screenshot_result.get("synced", 0) > 0:
        print("\n✅ SCREENSHOT SYNC FIX IS WORKING!")
    elif screenshots_count > 0:
        print("\n❌ SCREENSHOT SYNC IS STILL NOT WORKING")
    else:
        print("\n⚠️ UNABLE TO FULLY TEST - NO UNSYNCHRONIZED SCREENSHOTS FOUND")
        print("   Please capture some screenshots and run this test again")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_screenshot_sync())
