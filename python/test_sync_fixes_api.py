"""
Script to test the sync fixes for project_tasks and screenshots using the running application API.
This is a more direct test that works with the actual running application.

This script:
1. Resets the sync state for project_tasks and screenshots 
2. Calls the API endpoint to trigger a sync
3. Verifies the results
"""
import os
import sys
import json
import asyncio
import logging
import requests
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

# API settings
API_URL = "http://localhost:8000"  # Default API URL

async def test_sync_fixes_api():
    """Test the sync fixes using the running application API."""
    print("\n" + "="*50)
    print("TESTING SYNC FIXES USING THE APPLICATION API")
    print("="*50 + "\n")
    
    # Step 1: Check if the API is running
    print("\n[Step 1] Checking if the API is running...")
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is running")
        else:
            print(f"❌ API returned status code {response.status_code}")
            print("⚠️ Please start the application API with 'uvicorn api.main:app --reload'")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the API")
        print("⚠️ Please start the application API with 'uvicorn api.main:app --reload'")
        return False
    
    # Step 2: Reset sync state
    print("\n[Step 2] Resetting sync state for project_tasks and screenshots...")
    reset_result = reset_sync_state(['project_tasks', 'screenshots'])
    if not reset_result:
        print("⚠️ Could not reset sync state, but continuing anyway.")
    
    # Step 3: Get authentication token
    print("\n[Step 3] Retrieving current user authentication token...")
    try:
        response = requests.get(f"{API_URL}/auth/session")
        if response.status_code == 200:
            auth_data = response.json()
            token = auth_data.get("token")
            if token:
                print("✅ Retrieved authentication token")
            else:
                print("❌ No authentication token found in response")
                print("⚠️ Please start the application and login first")
                return False
        else:
            print(f"❌ Failed to get authentication session: {response.status_code}")
            print("⚠️ Please start the application and login first")
            return False
    except Exception as e:
        print(f"❌ Error retrieving authentication token: {str(e)}")
        return False
    
    # Set headers with authentication token
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Step 4: Trigger sync
    print("\n[Step 4] Triggering sync for project_tasks and screenshots...")
    try:
        response = requests.post(f"{API_URL}/sync/all", headers=headers)
        if response.status_code == 200:
            sync_result = response.json()
            print("✅ Sync operation completed")
            
            # Check individual sync results
            task_status = sync_result.get("tasks", {}).get("status", "unknown")
            screenshot_status = sync_result.get("screenshots", {}).get("status", "unknown")
            
            print(f"   Project tasks sync status: {task_status}")
            if task_status == "complete" or task_status == "partial":
                synced_tasks = sync_result.get("tasks", {}).get("synced", 0)
                if synced_tasks > 0:
                    print(f"   ✅ Successfully synced {synced_tasks} project tasks to Supabase")
                else:
                    print("   ℹ️ No project tasks were synced (either none to sync or there was an issue)")
            
            print(f"   Screenshots sync status: {screenshot_status}")
            if screenshot_status == "complete" or screenshot_status == "partial":
                synced_screenshots = sync_result.get("screenshots", {}).get("synced", 0)
                if synced_screenshots > 0:
                    print(f"   ✅ Successfully synced {synced_screenshots} screenshots to Supabase")
                else:
                    print("   ℹ️ No screenshots were synced (either none to sync or there was an issue)")
            
            # Print full result for reference
            print("\nFull sync result:")
            print(json.dumps(sync_result, indent=2))
        else:
            print(f"❌ Sync operation failed with status code {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Error triggering sync: {str(e)}")
        return False
    
    # Summary
    print("\n" + "="*50)
    print("VERIFICATION SUMMARY")
    print("="*50)
    
    print("\n✅ The test script has completed successfully.")
    
    if task_status == "complete" or task_status == "partial":
        if synced_tasks > 0:
            print("✅ Project tasks sync fix is WORKING!")
        else:
            print("ℹ️ Project tasks sync appears to be working, but no tasks were synced.")
            print("   Create a new project task and run this script again to fully verify.")
    else:
        print("⚠️ Project tasks sync status indicates a problem. Check the logs for details.")
    
    if screenshot_status == "complete" or screenshot_status == "partial":
        if synced_screenshots > 0:
            print("✅ Screenshots sync fix is WORKING!")
        else:
            print("ℹ️ Screenshots sync appears to be working, but no screenshots were synced.")
            print("   Capture a new screenshot and run this script again to fully verify.")
    else:
        print("⚠️ Screenshots sync status indicates a problem. Check the logs for details.")
    
    print("\nNext steps:")
    print("1. Continue using the application normally")
    print("2. Create new projects, tasks, and capture screenshots")
    print("3. Verify that everything syncs correctly with Supabase")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_sync_fixes_api())
