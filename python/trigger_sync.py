"""
Manual trigger for synchronization between local database and Supabase.
This script helps test if the sync fix resolves the synchronization issues.
"""
import asyncio
import logging
import os
import getpass
import time
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Make sure we load environment variables
load_dotenv()

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

async def run_manual_sync(auth_service=None):
    """Run a manual sync operation to test if screenshots are correctly synced."""
    try:
        # Dynamically import services to avoid circular imports
        from services.database import DatabaseService
        from services.supabase_auth import SupabaseAuthService
        from services.supabase_sync import SupabaseSyncService
        # Import extensions to patch the services with additional methods
        import services.init_service_extensions
        
        # Initialize database service
        logger.info("Creating database service...")
        db_service = DatabaseService()
        logger.info("Database service created")
            
        # If auth_service wasn't provided, create one
        if not auth_service:
            logger.info("Creating Supabase auth service...")
            auth_service = SupabaseAuthService()
            logger.info("Auth service created")
            
            # Check if authenticated
            if not hasattr(auth_service, 'is_authenticated') or not auth_service.is_authenticated():
                logger.error("Not authenticated to Supabase - please login first")
                return False
            
        logger.info(f"Using authenticated user: {auth_service.user.get('email')}")
        
        logger.info("Creating Supabase sync service...")
        sync_service = SupabaseSyncService(db_service, auth_service)
        logger.info("Sync service created")
        
        # Verify sync service has required attributes
        if not hasattr(sync_service, 'sync_all'):
            logger.error("Sync service doesn't have required methods")
            return False
            
        # Count unsynchronized items
        screenshots = db_service.get_unsynchronized_screenshots(0)
        screenshot_count = len(screenshots) if screenshots else 0
        logger.info(f"Found {screenshot_count} unsynchronized screenshots in local database")

        # Check for unsynchronized activity logs
        try:
            if hasattr(db_service, 'get_unsynchronized_time_entries'):
                activity_logs = db_service.get_unsynchronized_time_entries(0)
            else:
                activity_logs = db_service.get_unsynchronized_activity_logs(0)
            activity_count = len(activity_logs) if activity_logs else 0
            logger.info(f"Found {activity_count} unsynchronized activity logs in local database")
        except AttributeError:
            logger.warning("Could not check activity logs - method not found")
            activity_count = 0
        
        # Trigger full sync operation
        logger.info("Triggering full sync operation...")
        sync_result = await sync_service.sync_all()
        
        logger.info(f"Sync completed with status: {sync_result.get('status')}")
        
        # Log individual component results
        components = [
            ('activity_logs', 'Activity Logs'),
            ('screenshots', 'Screenshots'),
            ('clients', 'Clients'),
            ('projects', 'Projects'),
            ('project_tasks', 'Project Tasks'),
            ('user_profiles', 'User Profiles'),
            ('user_settings', 'User Settings')
        ]
        
        for key, name in components:
            if sync_result.get(key):
                logger.info(f"{name} sync result: {sync_result.get(key)}")
        
        # Verify if items were synced
        remaining_screenshots = db_service.get_unsynchronized_screenshots(0)
        remaining_screenshot_count = len(remaining_screenshots) if remaining_screenshots else 0
        logger.info(f"Remaining unsynchronized screenshots: {remaining_screenshot_count}")
        
        if screenshot_count > 0 and remaining_screenshot_count < screenshot_count:
            logger.info(f"SUCCESS! Synced {screenshot_count - remaining_screenshot_count} screenshots")
        elif screenshot_count > 0:
            logger.error("Failed to sync any screenshots")
            
        # Check activity logs sync status
        try:
            if hasattr(db_service, 'get_unsynchronized_time_entries'):
                remaining_activity_logs = db_service.get_unsynchronized_time_entries(0)
            else:
                remaining_activity_logs = db_service.get_unsynchronized_activity_logs(0)
                
            remaining_activity_count = len(remaining_activity_logs) if remaining_activity_logs else 0
            logger.info(f"Remaining unsynchronized activity logs: {remaining_activity_count}")
            
            if activity_count > 0 and remaining_activity_count < activity_count:
                logger.info(f"SUCCESS! Synced {activity_count - remaining_activity_count} activity logs")
            elif activity_count > 0:
                logger.error("Failed to sync any activity logs")
        except AttributeError:
            pass
        
        # Check all data types for sync status
        sync_checks = [
            ('clients', 'get_unsynchronized_clients', 'Clients'),
            ('projects', 'get_unsynchronized_projects', 'Projects'),
            ('project_tasks', 'get_unsynchronized_project_tasks', 'Project Tasks'),
            ('user_profiles', 'get_unsynchronized_user_profiles', 'User Profiles'),
            ('user_settings', 'get_unsynchronized_user_settings', 'User Settings')
        ]
        
        for result_key, method_name, display_name in sync_checks:
            try:
                # Check if the database service has the method
                if hasattr(db_service, method_name):
                    # Get the method and call it
                    method = getattr(db_service, method_name)
                    items = method('')
                    item_count = len(items)
                    
                    if item_count > 0:
                        logger.info(f"Found {item_count} unsynchronized {display_name.lower()} in local database")
                        if sync_result.get(result_key, {}).get('synced', 0) > 0:
                            logger.info(f"SUCCESS! Synced {sync_result.get(result_key, {}).get('synced', 0)} {display_name.lower()}")
            except Exception as e:
                logger.warning(f"Could not check {display_name.lower()} sync status: {str(e)}")
            
        return True
            
    except Exception as e:
        logger.error(f"Error in manual sync: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("=== Manual Sync Trigger ===")
    
    async def main():
        """Main entry point."""
        try:
            # Dynamically import services
            from services.supabase_auth import SupabaseAuthService
            
            # Create auth service
            auth_service = SupabaseAuthService()
            
            # Check if already authenticated
            if not auth_service.is_authenticated():
                logger.info("Not authenticated, starting login process...")
                if not await login_to_supabase(auth_service):
                    logger.error("Authentication failed. Please try again.")
                    return
            
            # Run the sync process with the authenticated auth service
            await run_manual_sync(auth_service)
            
        except Exception as e:
            logger.error(f"Error in main: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    # Run the main async function
    asyncio.run(main())
