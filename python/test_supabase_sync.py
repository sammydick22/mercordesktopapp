"""
Test script for Supabase synchronization integration.

This script tests the synchronization between local database and Supabase.
"""
import asyncio
import logging
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

from services.database import DatabaseService
from services.supabase_auth import SupabaseAuthService
from services.supabase_sync import SupabaseSyncService
from services.screenshots import ScreenshotManagementService
from services.activity import ActivityTrackingService
from utils.config import Config

# Check Python version
if sys.version_info < (3, 9):
    print("Error: Python 3.9 or higher is required for the Supabase client")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def generate_test_data(db_service, activity_service, screenshot_service):
    """Generate some test data for syncing if needed."""
    logger.info("Checking for existing data to sync...")
    
    # Check if we have activity logs to sync
    activity_logs = db_service.get_unsynchronized_activity_logs()
    screenshots = db_service.get_unsynchronized_screenshots()
    
    if activity_logs:
        logger.info(f"Found {len(activity_logs)} unsynchronized activity logs")
    else:
        logger.info("No existing activity logs to sync, creating some test data...")
        
        # Start activity tracking
        activity_service.start()
        
        # Create a few test activities
        for i in range(3):
            window_title = f"Test Window {i}"
            process_name = "test_supabase_sync.py"
            activity_service._start_new_activity({
                "window_title": window_title,
                "process_name": process_name,
                "executable_path": sys.executable
            })
            
            # Wait a bit
            await asyncio.sleep(1)
            
            # End the activity
            if activity_service.current_activity_id:
                activity_service._stop_current_activity()
        
        # Stop activity tracking
        activity_service.stop()
        
        # Verify activities were created
        activity_logs = db_service.get_unsynchronized_activity_logs()
        logger.info(f"Created {len(activity_logs)} test activity logs")
    
    if screenshots:
        logger.info(f"Found {len(screenshots)} unsynchronized screenshots")
    else:
        logger.info("No existing screenshots to sync, creating a test screenshot...")
        
        # Create a test screenshot
        screenshot_result = await screenshot_service.capture_screenshot()
        if screenshot_result:
            logger.info(f"Created test screenshot: {screenshot_result['filepath']}")
        else:
            logger.warning("Failed to create test screenshot")
    
    return True

async def test_sync_flow():
    """Test the full synchronization flow with Supabase."""
    logger.info("Starting Supabase synchronization test")
    
    # Initialize services
    config = Config()
    db_service = DatabaseService(config)
    auth_service = SupabaseAuthService()
    activity_service = ActivityTrackingService(config, db_service)
    screenshot_service = ScreenshotManagementService(config, db_service, activity_service)
    sync_service = SupabaseSyncService(db_service, auth_service)
    
    # Check if we have environment variables
    if not sync_service.supabase_url or not sync_service.supabase_key:
        logger.error("Missing Supabase URL or key in environment variables")
        return False
    
    logger.info(f"Supabase URL: {sync_service.supabase_url}")
    logger.info(f"Supabase Key: {sync_service.supabase_key[:5]}...")
    
    # Check if Supabase client was initialized
    if not sync_service.supabase:
        logger.error("Supabase client was not initialized successfully")
        return False
    
    logger.info("Supabase client initialized successfully")
    
    # Test user credentials - replace with test user credentials
    # WARNING: Don't use production credentials here!
    test_email = input("Enter test email: ")
    test_password = input("Enter test password: ")
    
    try:
        # Step 1: Sign in
        logger.info("Authenticating with Supabase...")
        auth_data = await auth_service.sign_in_with_email(test_email, test_password)
        if not auth_data or not auth_data.get("user"):
            logger.error("Authentication failed or user data missing")
            return False
            
        user_id = auth_data["user"].get("id")
        logger.info(f"Authentication successful. User ID: {user_id}")
        
        # Step 2: Initialize sync service
        logger.info("Initializing sync service...")
        init_result = await sync_service.initialize()
        if not init_result:
            logger.error("Failed to initialize sync service")
            return False
        logger.info("Sync service initialized successfully")
        
        # Step 3: Generate test data if needed
        await generate_test_data(db_service, activity_service, screenshot_service)
        
        # Step 4: Sync organization data from Supabase to local database
        logger.info("Syncing organization data...")
        org_result = await sync_service.sync_organization_data()
        logger.info(f"Organization sync result: {org_result['status']}")
        
        # Step 5: Sync activity logs from local database to Supabase
        logger.info("Syncing activity logs...")
        activity_result = await sync_service.sync_activity_logs()
        logger.info(f"Activity logs sync result: {activity_result}")
        logger.info(f"Synced: {activity_result['synced']}, Failed: {activity_result['failed']}")
        
        # Step 6: Sync screenshots from local storage to Supabase Storage
        logger.info("Syncing screenshots...")
        screenshots_result = await sync_service.sync_screenshots()
        logger.info(f"Screenshots sync result: {screenshots_result}")
        logger.info(f"Synced: {screenshots_result['synced']}, Failed: {screenshots_result['failed']}")
        
        # Step 7: Test sync_all convenience method
        logger.info("Testing sync_all method...")
        sync_all_result = await sync_service.sync_all()
        logger.info(f"Sync all result: {sync_all_result['status']}")
        
        # Step 8: Sign out
        logger.info("Signing out...")
        sign_out_result = await auth_service.sign_out()
        logger.info(f"Sign out result: {sign_out_result}")
        
        return True
    except Exception as e:
        logger.error(f"Synchronization test failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("=== Supabase Synchronization Test ===")
    print("This script tests synchronization with Supabase")
    print("Make sure you have the following in your .env file:")
    print("  SUPABASE_URL=your-supabase-project-url")
    print("  SUPABASE_ANON_KEY=your-supabase-anon-key")
    print()
    print("Your Supabase project should have these tables:")
    print("  - activity_logs")
    print("  - screenshots")
    print("  - organizations")
    print("  - org_members")
    print()
    print("And a storage bucket named 'screenshots'")
    print("=================================\n")
    
    try:
        success = asyncio.run(test_sync_flow())
        
        if success:
            logger.info("✅ All synchronization tests passed!")
            exit(0)
        else:
            logger.error("❌ Synchronization tests failed!")
            exit(1)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        exit(1)
