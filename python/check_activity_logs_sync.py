"""
Diagnostic script for activity logs synchronization issues.
"""
import asyncio
import logging
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Make sure we load environment variables
load_dotenv()

async def create_test_activity_log():
    """Create a test activity log in the local database."""
    try:
        # Dynamically import services
        from services.database import DatabaseService
        
        # Initialize database service
        logger.info("Creating database service...")
        db_service = DatabaseService()
        logger.info("Database service created")
        
        # Get connection to database for direct queries
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        # Create a test activity log that is definitely not synced
        logger.info("Creating test activity log...")
        cursor.execute(
            """
            INSERT INTO activity_logs 
            (window_title, process_name, executable_path, start_time, end_time, duration, is_active, synced, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """,
            (
                "Test Window", 
                "test_process.exe",
                "C:\\test\\path\\test_process.exe",
                "2025-03-24T13:47:00.000Z",
                "2025-03-24T13:48:00.000Z",
                60,  # 1 minute in seconds
                0,   # not active
                0,   # not synced
            )
        )
        
        # Commit the changes
        conn.commit()
        
        # Verify the activity log was created
        cursor.execute("SELECT last_insert_rowid()")
        log_id = cursor.fetchone()[0]
        
        logger.info(f"Successfully created test activity log with ID: {log_id}")
        return log_id
        
    except Exception as e:
        logger.error(f"Error creating test activity log: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

async def check_unsynchronized_activity_logs():
    """Check for unsynchronized activity logs in the database."""
    try:
        # Dynamically import services
        from services.database import DatabaseService
        
        # Import extensions to patch services with additional methods
        import services.init_service_extensions
        
        # Initialize database service
        logger.info("Creating database service...")
        db_service = DatabaseService()
        logger.info("Database service created")
        
        # First check direct SQL to see all activity logs
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        logger.info("Checking all activity logs...")
        cursor.execute(
            """
            SELECT id, window_title, synced
            FROM activity_logs
            ORDER BY id DESC
            LIMIT 10
            """
        )
        
        all_logs = cursor.fetchall()
        logger.info(f"Found {len(all_logs)} activity logs in database")
        for log in all_logs:
            logger.info(f"Activity log: id={log[0]}, title={log[1]}, synced={log[2]}")
        
        logger.info("Checking for unsynchronized activity logs...")
        cursor.execute(
            """
            SELECT id, window_title
            FROM activity_logs
            WHERE synced = 0
            ORDER BY id DESC
            """
        )
        
        unsynced_logs = cursor.fetchall()
        logger.info(f"Found {len(unsynced_logs)} unsynchronized activity logs via direct SQL")
        for log in unsynced_logs:
            logger.info(f"Unsynced log: id={log[0]}, title={log[1]}")
            
        # Now use the extension method to see if it's working
        try:
            logger.info("Trying to get unsynchronized activity logs via extension method...")
            extension_logs = db_service.get_unsynchronized_activity_logs()
            logger.info(f"Found {len(extension_logs)} unsynchronized activity logs via extension method")
            for log in extension_logs:
                logger.info(f"Extension unsynced log: id={log['id']}, title={log['window_title']}")
                
            return len(extension_logs)
        except Exception as e:
            logger.error(f"Error using extension method: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return 0
            
    except Exception as e:
        logger.error(f"Error checking unsynchronized activity logs: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 0

async def debug_sync_activity_logs():
    """Debug the sync_activity_logs method."""
    try:
        # Dynamically import services
        from services.database import DatabaseService
        from services.supabase_auth import SupabaseAuthService
        from services.supabase_sync import SupabaseSyncService
        
        # Import extensions to patch services with additional methods
        import services.init_service_extensions
        
        # Initialize services
        logger.info("Creating services...")
        db_service = DatabaseService()
        auth_service = SupabaseAuthService()
        
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
        
        # Create sync service
        sync_service = SupabaseSyncService(db_service, auth_service)
        
        # Check if the sync_activity_logs method exists
        if not hasattr(sync_service, 'sync_activity_logs'):
            logger.error("sync_activity_logs method does not exist on sync service!")
            return False
            
        # Try to run the sync_activity_logs method directly
        logger.info("Attempting to call sync_activity_logs method directly...")
        result = await sync_service.sync_activity_logs()
        
        logger.info(f"Sync activity logs result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error debugging sync_activity_logs: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

async def main():
    """Run the diagnostic checks."""
    logger.info("=== ACTIVITY LOGS SYNC DIAGNOSTICS ===")
    
    # Create a test activity log
    await create_test_activity_log()
    
    # Check for unsynchronized activity logs
    unsynced_count = await check_unsynchronized_activity_logs()
    
    if unsynced_count > 0:
        # Debug sync_activity_logs
        result = await debug_sync_activity_logs()
        
        if result:
            logger.info(f"Sync activity logs completed with status: {result.get('status')}")
            logger.info(f"Synced: {result.get('synced')}, Failed: {result.get('failed')}")
        else:
            logger.error("Failed to sync activity logs")
    else:
        logger.warning("No unsynchronized activity logs found to test sync with")
    
    logger.info("=== DIAGNOSTICS COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(main())
