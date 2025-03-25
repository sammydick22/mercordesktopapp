"""
Test script to verify that the screenshot sync fix is working correctly.
"""
import os
import sys
import asyncio
import logging
import getpass
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Make sure we load environment variables
load_dotenv()

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our services
from services.database import DatabaseService
from services.supabase_auth import SupabaseAuthService
from services.supabase_sync import SupabaseSyncService
from reset_sync_state import reset_sync_state

async def login_to_supabase(auth_service):
    """Prompt for login credentials and authenticate with Supabase."""
    # Check if we have a saved session first
    session_path = os.path.expanduser("~/TimeTracker/data/session.json")
    if os.path.exists(session_path):
        logger.info("Found saved session, attempting to load...")
        if auth_service.load_session(session_path):
            logger.info("Session loaded successfully")
            if auth_service.is_authenticated():
                logger.info("Session is valid")
                return True
            else:
                logger.info("Session is expired or invalid")
    
    # If we get here, we need to log in
    print("\n=== Supabase Login ===")
    email = input("Email: ")
    password = getpass.getpass("Password: ")
    
    try:
        logger.info("Attempting to sign in...")
        auth_data = await auth_service.sign_in_with_email(email, password)
        logger.info(f"Successfully logged in as {auth_data['user']['email']}")
        
        # Save session for future use
        os.makedirs(os.path.dirname(session_path), exist_ok=True)
        auth_service.save_session(session_path)
        logger.info(f"Session saved to {session_path}")
        
        return True
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        return False

async def verify_screenshot_sync():
    """Verify that screenshot sync fix works correctly."""
    print("\n" + "="*60)
    print(" TESTING IMPROVED SCREENSHOT SYNC IMPLEMENTATION")
    print("="*60 + "\n")
    
    # Step 1: Reset the screenshots sync state
    print("\n[Step 1] Resetting screenshots sync state...")
    try:
        reset_result = reset_sync_state(['screenshots'])
        if reset_result:
            print("✅ Successfully reset screenshots sync state")
        else:
            print("⚠️ Could not reset sync state, but continuing anyway.")
    except Exception as e:
        print(f"⚠️ Error resetting sync state: {e}")
        print("Continuing with the test anyway.")
    
    # Step 2: Initialize services
    print("\n[Step 2] Initializing services...")
    db_service = DatabaseService()
    auth_service = SupabaseAuthService()
    sync_service = SupabaseSyncService(db_service, auth_service)
    
    # Step 3: Check authentication
    print("\n[Step 3] Checking authentication status...")
    is_auth = auth_service.is_authenticated()
    if not is_auth:
        print("Not authenticated, attempting to login...")
        is_auth = await login_to_supabase(auth_service)
        if not is_auth:
            print("❌ Authentication failed. Please try again.")
            return False
    
    user = await auth_service.get_user() 
    print(f"✅ Authenticated as user: {user.get('email')}")
    
    # Step 4: Check for unsynchronized screenshots
    print("\n[Step 4] Checking for unsynchronized screenshots...")
    screenshots = db_service.get_unsynchronized_screenshots(None)
    
    if not screenshots:
        print("⚠️ No unsynchronized screenshots found. No need to test sync.")
        screenshots_count = 0
    else:
        screenshots_count = len(screenshots)
        print(f"✅ Found {screenshots_count} unsynchronized screenshots")
        
        # Print a sample screenshot for verification
        if screenshots_count > 0:
            sample = screenshots[0]
            print(f"   Sample screenshot ID: {sample['id']}")
            print(f"   Filepath: {sample.get('filepath', 'Not available')}")
            print(f"   Time entry ID: {sample.get('time_entry_id', 'Not available')}")
            print(f"   Created at: {sample.get('created_at', 'Not available')}")
    
    # Step 5: Initialize sync service
    print("\n[Step 5] Initializing sync service...")
    init_result = await sync_service.initialize()
    if not init_result:
        print("❌ Failed to initialize sync service.")
        return False
    print("✅ Sync service initialized successfully")
    
    # Step 6: Test screenshots sync
    if screenshots_count > 0:
        print("\n[Step 6] Testing screenshot sync...")
        screenshot_result = await sync_service.sync_screenshots()
        
        if screenshot_result.get("status") in ["complete", "partial"]:
            if screenshot_result.get("synced", 0) > 0:
                print(f"✅ Successfully synced {screenshot_result.get('synced')} screenshots")
                
                # Check if we synced all screenshots
                if screenshot_result.get("synced") == screenshots_count:
                    print("✅ All screenshots were successfully synced!")
                else:
                    print(f"⚠️ Only {screenshot_result.get('synced')} out of {screenshots_count} screenshots were synced.")
            else:
                print("⚠️ No screenshots were synced. There might still be an issue.")
                print(f"   Screenshot sync result: {screenshot_result}")
        else:
            print(f"❌ Screenshots sync failed with status: {screenshot_result.get('status')}")
            print(f"   Error details: {screenshot_result}")
    else:
        print("\n[Step 6] Skipping screenshot sync test since no unsynchronized screenshots were found")
    
    # Summary
    print("\n" + "="*60)
    print(" SUMMARY")
    print("="*60)
    
    if screenshots_count > 0 and screenshot_result.get("synced", 0) > 0:
        print("\n✅ SCREENSHOT SYNC FIX IS WORKING!")
        print(f"   Successfully synced {screenshot_result.get('synced')} out of {screenshots_count} screenshots")
    elif screenshots_count > 0:
        print("\n❌ SCREENSHOT SYNC IS STILL NOT WORKING")
        print(f"   Failed to sync any of the {screenshots_count} unsynchronized screenshots")
    else:
        print("\n⚠️ UNABLE TO FULLY TEST - NO UNSYNCHRONIZED SCREENSHOTS FOUND")
        print("   Please capture some screenshots and run this test again")
    
    print("\nDone!")
    return True

if __name__ == "__main__":
    asyncio.run(verify_screenshot_sync())
