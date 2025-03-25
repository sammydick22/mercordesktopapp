"""
Debug script to identify why activity logs aren't being synced.
"""
import asyncio
import logging
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Using DEBUG level to get more detailed info
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Make sure we load environment variables
load_dotenv()

async def debug_sync_activity_logs():
    """Debug the activity logs syncing logic by explicitly mocking each step."""
    
    # Import dependencies
    from services.supabase_auth import SupabaseAuthService
    from services.database import DatabaseService
    from services.supabase_sync import SupabaseSyncService
    
    # Import extensions
    import services.init_service_extensions
    
    # Create services
    logger.info("Creating services...")
    db_service = DatabaseService()
    auth_service = SupabaseAuthService()
    
    # Patch sync_activity_logs to detect issues
    original_sync_method = SupabaseSyncService.sync_activity_logs
    
    async def patched_sync_method(self, *args, **kwargs):
        """Patched version that adds extra debug logging."""
        logger.debug("=== PATCHED SYNC METHOD CALLED ===")
        
        # Debug auth service state
        logger.debug(f"Auth service authenticated? {auth_service.is_authenticated()}")
        logger.debug(f"Auth user: {auth_service.user}")
        
        # Debug user ID and org ID
        user_id = self.auth_service.user.get("id") if self.auth_service.user else None
        logger.debug(f"User ID from auth service: {user_id}")
        
        # Debug org ID lookup
        if user_id:
            org_membership = self.db_service.get_user_org_membership(user_id)
            logger.debug(f"Org membership from DB: {org_membership}")
            
            # Debug the org ID that would be used
            org_id = org_membership['org_id'] if org_membership else None
            logger.debug(f"Org ID from local DB: {org_id}")
            
            # Get unsynchronized logs
            try:
                # Count of unsynchronized logs
                conn = self.db_service._get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM activity_logs WHERE synced = 0")
                unsynced_count = cursor.fetchone()[0]
                logger.debug(f"Total unsynchronized activity logs: {unsynced_count}")
                
                # Get last ID from sync state
                last_sync_id = self.last_sync.get("activity_logs", {}).get("last_id", 0)
                logger.debug(f"Last sync ID from state: {last_sync_id}")
                
                # Count logs after last ID
                cursor.execute("SELECT COUNT(*) FROM activity_logs WHERE synced = 0 AND id > ?", 
                               (last_sync_id,))
                count_after_last_id = cursor.fetchone()[0]
                logger.debug(f"Unsynchronized logs after last_id={last_sync_id}: {count_after_last_id}")
                
                # Get logs using the method that would be used in sync
                logs = self.db_service.get_unsynchronized_activity_logs(last_sync_id)
                logger.debug(f"Retrieved {len(logs)} logs using get_unsynchronized_activity_logs")
                
                if logs:
                    logger.debug(f"First log: {logs[0]}")
                    logger.debug(f"Last log: {logs[-1]}")
                else:
                    logger.debug("No logs returned from get_unsynchronized_activity_logs")
            except Exception as e:
                logger.error(f"Error getting unsynchronized logs: {str(e)}", exc_info=True)
        
        # Call original method
        logger.debug("Calling original sync method...")
        result = await original_sync_method(self, *args, **kwargs)
        logger.debug(f"Original method result: {result}")
        return result
    
    # Replace the method with our patched version
    SupabaseSyncService.sync_activity_logs = patched_sync_method
    
    # Load session if available
    session_path = os.path.expanduser("~/TimeTracker/data/session.json")
    if os.path.exists(session_path):
        logger.info(f"Loading session from {session_path}")
        auth_service.load_session(session_path)
        
    # Create sync service with patched method
    sync_service = SupabaseSyncService(db_service, auth_service)
    
    # Try to run sync
    logger.info("Starting activity logs sync...")
    result = await sync_service.sync_activity_logs()
    
    logger.info(f"Activity logs sync result: {result}")
    return result

if __name__ == "__main__":
    logger.info("=== ACTIVITY LOGS SYNC DEBUGGING ===")
    asyncio.run(debug_sync_activity_logs())
    logger.info("=== DEBUGGING COMPLETE ===")
