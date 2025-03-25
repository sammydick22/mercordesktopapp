"""
Create a test time entry in the local database and trigger sync to verify synchronization.
"""
import asyncio
import logging
import os
import datetime
import uuid
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Make sure we load environment variables
load_dotenv()

async def create_time_entry_and_sync():
    """Create a test time entry and trigger synchronization."""
    try:
        # Dynamically import services
        from services.database import DatabaseService
        from services.supabase_auth import SupabaseAuthService
        from services.supabase_sync import SupabaseSyncService
        
        # Import extensions to patch the services with additional methods
        import services.init_service_extensions
        
        # Initialize database service
        logger.info("Creating database service...")
        db_service = DatabaseService()
        logger.info("Database service created")
        
        # Initialize auth service
        logger.info("Creating Supabase auth service...")
        auth_service = SupabaseAuthService()
        logger.info("Auth service created")
        
        # Check if authenticated
        if not hasattr(auth_service, 'is_authenticated') or not auth_service.is_authenticated():
            # Check if we have a saved session
            session_path = os.path.expanduser("~/TimeTracker/data/session.json")
            if os.path.exists(session_path):
                logger.info("Found saved session, attempting to load...")
                if auth_service.load_session(session_path):
                    logger.info("Session loaded successfully")
                    if auth_service.is_authenticated():
                        logger.info("Session is valid")
                    else:
                        logger.error("Session is expired or invalid")
                        return False
                else:
                    logger.error("Failed to load session")
                    return False
            else:
                logger.error("No saved session found")
                return False
        
        logger.info(f"Using authenticated user: {auth_service.user.get('email')}")
        
        # Create a new time entry in the local database
        logger.info("Creating a test time entry...")
        
        # Get connection to database
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        # Generate a unique time entry ID
        entry_id = str(uuid.uuid4())
        
        # Current timestamp
        now = datetime.datetime.now()
        
        # Create start time 30 minutes ago
        start_time = (now - datetime.timedelta(minutes=30)).isoformat()
        
        # Insert activity log (time entry)
        cursor.execute(
            """
            INSERT INTO activity_logs 
            (id, window_title, process_name, executable_path, start_time, end_time, duration, 
             is_active, synced, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry_id,
                "Test Time Entry - Coding Window",
                "VS Code",
                "C:\\Program Files\\Microsoft VS Code\\Code.exe",
                start_time,
                now.isoformat(),  # End time is now
                1800,  # Duration in seconds (30 minutes)
                0,  # Not active
                0,  # Not synced
                now.isoformat(),
                now.isoformat()
            )
        )
        
        # Commit the changes
        conn.commit()
        logger.info(f"Created test time entry with ID: {entry_id}")
        
        # Create sync service
        logger.info("Creating Supabase sync service...")
        sync_service = SupabaseSyncService(db_service, auth_service)
        logger.info("Sync service created")
        
        # Get unsynchronized time entries to confirm entry was created
        try:
            if hasattr(db_service, 'get_unsynchronized_time_entries'):
                entries = db_service.get_unsynchronized_time_entries(0)
            else:
                entries = db_service.get_unsynchronized_activity_logs(0)
            
            logger.info(f"Found {len(entries)} unsynchronized time entries")
            
            if entries:
                logger.info(f"Sample entry: {entries[0]}")
        except Exception as e:
            logger.error(f"Error getting unsynchronized entries: {str(e)}")
            return False
        
        # Sync time entries specifically rather than using sync_all
        logger.info("Syncing time entries...")
        try:
            # Use the sync_activity_logs method directly
            result = await sync_service.sync_activity_logs()
            logger.info(f"Sync result: {result}")
            
            # Check for successful sync
            if result.get("synced", 0) > 0:
                logger.info(f"SUCCESS! Synced {result.get('synced')} time entries")
            else:
                logger.error(f"Failed to sync time entries: {result}")
                
            return True
            
        except Exception as e:
            logger.error(f"Error in sync process: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
            
    except Exception as e:
        logger.error(f"Error in test: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("=== Creating Test Time Entry ===")
    asyncio.run(create_time_entry_and_sync())
